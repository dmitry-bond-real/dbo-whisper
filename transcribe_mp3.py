import argparse
import importlib
import re
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
import torch
import whisper


def get_torch_directml() -> Any | None:
    try:
        return importlib.import_module("torch_directml")
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe an MP3 file and save transcript as a TXT file with the same base name."
    )
    parser.add_argument("mp3_file", help="Path to the MP3 file to transcribe")
    parser.add_argument(
        "--model",
        default="base",
        help="Whisper model to use (tiny, base, small, medium, large)",
    )
    parser.add_argument(
        "--output",
        help="Optional output TXT path. Defaults to input name with .txt extension.",
    )
    parser.add_argument(
        "--marker",
        help="Optional string to include in the default output filename after the model name.",
    )
    parser.add_argument(
        "--formatting",
        choices=("wrap", "dot"),
        default="dot",
        help="Transcript formatting mode. 'wrap' wraps long lines; 'dot' starts a new line after each period-terminated phrase.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda", "dml"),
        default="auto",
        help="Execution device. Defaults to auto, which prefers CUDA, then DirectML, then CPU.",
    )
    parser.add_argument(
        "--transcribe-option",
        choices=("default", "static", "tradeoff"),
        default="tradeoff",
        help="Choose the transcription option preset: Whisper defaults, deterministic static decoding, or the current tradeoff profile.",
    )
    return parser.parse_args()


def has_directml() -> bool:
    return get_torch_directml() is not None


def resolve_device(device: str) -> str:
    if device == "auto":
        if torch.cuda.is_available():
            return "cuda"
        if has_directml():
            return "dml"
        return "cpu"

    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested, but this Python environment does not have CUDA support. "
            "Install a CUDA-enabled PyTorch build and verify torch.cuda.is_available() is True."
        )

    if device == "dml":
        if not has_directml():
            raise RuntimeError(
                "DirectML was requested, but torch-directml is not installed. "
                "Run: python -m pip install torch-directml"
            )

    return device


def load_model(model_name: str, resolved_device: str) -> torch.nn.Module:
    if resolved_device != "dml":
        return whisper.load_model(model_name, device=resolved_device)

    # DirectML workaround: load model on CPU first, then move to DML.
    model = whisper.load_model(model_name, device="cpu")

    # Whisper stores alignment_heads as sparse; sparse conversion to DML can fail.
    if getattr(model, "alignment_heads", None) is not None and model.alignment_heads.is_sparse:
        model.alignment_heads = model.alignment_heads.to_dense()

    torch_directml = get_torch_directml()
    return model.to(torch_directml.device())


def describe_model_device(model: torch.nn.Module, resolved_device: str) -> str:
    model_device = next(model.parameters()).device
    if model_device.type == "cuda":
        gpu_index = model_device.index if model_device.index is not None else torch.cuda.current_device()
        return f"cuda:{gpu_index} ({torch.cuda.get_device_name(gpu_index)})"

    if resolved_device == "dml":
        return f"dml ({model_device})"

    return resolved_device


def read_mp3_tags(input_path: Path) -> tuple[str, str]:
    try:
        tags = EasyID3(str(input_path))
    except (ID3NoHeaderError, MutagenError, OSError):
        return "", ""

    album = " ".join(part.strip() for part in tags.get("album", []) if part.strip())
    title = " ".join(part.strip() for part in tags.get("title", []) if part.strip())
    return album, title


def read_mp3_recording_info(input_path: Path) -> tuple[str, str]:
    recorded_at = ""
    duration = ""

    try:
        id3_tags = ID3(str(input_path))
        for frame_name in ("TDTG", "TDRC", "TDRL", "TDEN", "TDOR"):
            frame = id3_tags.get(frame_name)
            if frame and frame.text:
                recorded_at = str(frame.text[0]).strip()
                if recorded_at:
                    break
    except (ID3NoHeaderError, MutagenError, OSError):
        recorded_at = ""

    try:
        audio = MutagenFile(str(input_path))
        if audio is not None and getattr(audio, "info", None) is not None:
            length_seconds = int(round(getattr(audio.info, "length", 0)))
            hours, remainder = divmod(length_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (MutagenError, OSError, TypeError, ValueError):
        duration = ""

    return recorded_at, duration


def format_transcript_text(transcript: str, formatting: str, width: int = 75) -> str:
    if not transcript:
        return ""

    if formatting == "dot":
        phrases = [phrase.strip() for phrase in re.split(r"(?<=\.)\s+", transcript) if phrase.strip()]
        return "\n".join(phrases)

    return textwrap.fill(transcript, width=width)


def build_transcribe_options(variant: str) -> dict[str, Any]:
    if variant == "default":
        return {
            "word_timestamps": True,
        }

    if variant == "static":
        return {
            "word_timestamps": True,
            "temperature": 0.0,
            "best_of": 1,
            "beam_size": 1,
        }

    return {
        "word_timestamps": True,
        "temperature": (0.0, 0.2, 0.4),
        "beam_size": 5,
        "best_of": 5,
    }


def print_trailing_blank_lines() -> None:
    print()
    print()


def main() -> int:
    args = parse_args()

    input_path = Path(args.mp3_file).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    if input_path.suffix.lower() != ".mp3":
        print("Error: Input file must have .mp3 extension.")
        return 1

    output_name_parts = [input_path.stem, args.model]
    if args.marker:
        output_name_parts.append(args.marker)

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_name(".".join(output_name_parts) + ".txt")
    )

    try:
        album, title = read_mp3_tags(input_path)
        recorded_at, duration = read_mp3_recording_info(input_path)
        resolved_device = resolve_device(args.device)
        model = load_model(args.model, resolved_device)
        actual_device = describe_model_device(model, resolved_device)
        start_time = time.perf_counter()
        print(f"Transcription started at: {datetime.now().astimezone().isoformat()}")
        print(f"Actual device: {actual_device}, trns_option: {args.transcribe_option}")

        transcribe_options = build_transcribe_options(args.transcribe_option)
        if resolved_device == "dml":
            # Cross-attention timing path can be unstable on DML; disable for compatibility.
            transcribe_options["word_timestamps"] = False
            print("DirectML compatibility mode: word_timestamps disabled.")

        result = model.transcribe(str(input_path), **transcribe_options)
        transcription_seconds = time.perf_counter() - start_time
        transcript = result.get("text", "").strip()
        formatted_transcript = format_transcript_text(transcript, args.formatting)

        ts = datetime.now().astimezone().isoformat()
        output_lines = [
            f"album: {album}", 
            f"title: {title}", 
            f"recorded_at: {recorded_at}",
            f"duration: {duration}",
            f"transcribing_device: {actual_device}", 
            f"transcribed_at: {ts} using model: {args.model}", 
            f"formatting: {args.formatting}",
            f"transcribe_option: {args.transcribe_option}",
            "",
            formatted_transcript
            ]
        output_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")
        print(f"Transcription finished at: {ts}")
        print(f"Transcript saved to: {output_path}")
        print(f"Device used: {actual_device}")
        print(f"Transcription time: {transcription_seconds:.2f} seconds")
        print_trailing_blank_lines()
        return 0
    except Exception as exc:
        print(f"Error during transcription: {exc}")
        print_trailing_blank_lines()
        return 1


if __name__ == "__main__":
    sys.exit(main())
