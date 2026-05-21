# MP3 Transcriber

The purpose: **I have a tons of `*.MP3` files produced by `Desktop Call Recoder`**. 
Most of them are recording of our standup meetings. 
Some - calls with customers.
Some - calls with coleagues.
**The problem - I remember *we discussed something*, but with the time passed 
it because hard to remember - when we discussed that and what was decision**.
So, by this app I'm just trying to transcribe all my meeting records 
with idea to pass them though the AI.

**Also a problem** - in most cases I run it on my main PC (with NVIDIA video card). 
But sometimes I have to run it on corporate laptop with integrated AMD video card.
That is why need to support - all possible runtime options: *CUDA, DirectML, CPU*.

Thus, this is...
  Python CLI app that transcribes an MP3 file with OpenAI Whisper and writes a TXT file containing MP3 metadata plus the transcript.

The output file currently includes:

- `album`
- `title`
- `recorded_at`
- `duration`
- `transcribing_device`
- `transcribed_at`
- `formatting`
- transcript body

## Requirements

- Windows with Python 3.12
- `ffmpeg` available on `PATH`
- One of these acceleration targets:
- NVIDIA GPU with CUDA for `--device cuda`
- DirectML-capable environment for `--device dml`
- CPU works as a fallback

## Dependency Files

This repo uses split requirement files so CUDA and DirectML do not conflict in the same environment.

- `requirements-base.txt`: shared application dependencies
- `requirements-cuda.txt`: shared dependencies plus CUDA PyTorch packages
- `requirements-dml.txt`: shared dependencies plus `torch-directml`

Do not install both backend-specific files into the same virtual environment.

## Environment Setup

Create separate virtual environments:

```powershell
py -3.12 -m venv .venv-cuda
py -3.12 -m venv .venv-dml
```

### CUDA Environment

Use this on the NVIDIA/CUDA machine.

```powershell
& .\.venv-cuda\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements-cuda.txt
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

Expected check:

- `torch.version.cuda` is not `None`
- `torch.cuda.is_available()` is `True`

### DirectML Environment

Use this on the DirectML machine.

```powershell
& .\.venv-dml\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements-dml.txt
python -c "import importlib, torch; print(torch.__version__); print(torch.cuda.is_available()); print(importlib.import_module('torch_directml').device())"
```

Expected check:

- `torch.cuda.is_available()` is usually `False`
- `torch_directml.device()` returns something like `privateuseone:0`

## Usage

Basic usage:

```powershell
python .\transcribe_mp3.py "path\to\audio.mp3"
```

Default output filename:

```text
{sourceFilename}.{model}.txt
```

If `--marker` is provided:

```text
{sourceFilename}.{model}.{marker}.txt
```

If `--output` is provided, that path is used instead of the default generated name.

## CLI Options

- `mp3_file`: input MP3 path
- `--model`: Whisper model name, default `base`
- `--output`: explicit output TXT path
- `--marker`: optional string appended to the generated output filename after the model name
- `--formatting {wrap,dot}`: transcript output style, default `dot`
- `--device {auto,cpu,cuda,dml}`: execution backend, default `auto`
- `--transcribe-option {default,tradeoff,static}`: selection of transcribing options set

## Formatting Modes

`wrap`

- Wraps long transcript lines at 75 characters

`dot`

- Splits the transcript into one line per phrase by starting a new line after each period

## Examples

CUDA run:

```powershell
& .\.venv-cuda\Scripts\Activate.ps1
python .\transcribe_mp3.py "v00\2026\2026_01_20 06-30-34.mp3" --model medium --device cuda
```

DirectML run:

```powershell
& .\.venv-dml\Scripts\Activate.ps1
python .\transcribe_mp3.py "v00\2026\2026_01_20 06-30-34.mp3" --model small --device dml
```

Wrapped transcript with marker:

```powershell
python .\transcribe_mp3.py "v00\2026\2026_01_20 06-30-34.mp3" --model small --marker tc1 --formatting wrap
```

Dot-formatted transcript:

```powershell
python .\transcribe_mp3.py "v00\2026\2026_01_20 06-30-34.mp3" --model small --formatting dot
```

## Notes

- `--device auto` prefers CUDA, then DirectML, then CPU
- `--device cuda` requires a CUDA-enabled PyTorch build
- `--device dml` requires `torch-directml`
- DirectML runs in compatibility mode with `word_timestamps` disabled
- `recorded_at` depends on timestamp metadata being present in the MP3 tags


# Test Cases Script

```shell
@echo off

rem .\.venv-cuda\scripts\activate.ps1
rem .\.venv-dml\scripts\activate.ps1

echo compile PY...
py -3.12 -m py_compile transcribe_mp3.py

set dev=cuda
if "%1" == "" goto skip1
  set dev=%1
:skip1

echo = device: %dev%

set srcFile="v00\2026\2026_01_20 06-30-34.mp3"
echo = srcFile: %srcFile%

set trxOpt=--transcribe-option static
echo = transcribeOption: %srcFile%

set model=small
echo = model: %model%
set opts=--model %model% --device %dev% --marker %dev%-tc1 --formatting dot %trxOpt%
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

set model=medium
echo = model: %model%
set opts=--model %model% --device %dev% --formatting dot --transcribe-option static
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

set model=large
echo = model: %model%
set opts=--model %model% --device %dev% --marker %dev%-tc1 --formatting dot --transcribe-option static
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

title "%DATE%,%TIME% COMPLETED"
```

This script producing files like these:
- 2026_01_20 06-30-34.large.cuda-tc1.txt
- 2026_01_20 06-30-34.medium.cuda-tc2.txt
- 2026_01_20 06-30-34.small.cuda-tc3.txt

Thus, I can compare different iterations of transcribing process.


Example of header in each file:
```
album: Desktop call recorder | Microsoft Teams
title: MrhOp Daily Stand Up | Microsoft Teams
recorded_at: 2026-01-20 06:30:34
duration: 00:34:43
transcribing_device: cuda:0 (NVIDIA GeForce RTX 3060)
transcribed_at: 2026-05-21T17:34:52.013624+03:00 using model: large
formatting: dot
transcribe_option: static

Good morning everyone.
Good morning.
Good morning everyone.
Hi everyone, good morning.
Hi team, good morning.
[...]
```
