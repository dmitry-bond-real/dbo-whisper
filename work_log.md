
# App

## Initial AI prompt
```
role: Python and AI expert
task:
  create a simple python app which will take name of mp3 file as parameter, 
  generate transcript of it and save with the same name but with txt file name extension
```


# Further Code Adjustments

## need to how much time was spent on preparing transcript

    start_time = time.perf_counter()
    result = model.transcribe(str(input_path), response_format="srt")
    transcription_seconds = time.perf_counter() - start_time

## is it possible to change to use CUDA instead of CPU 

> python transcribe_mp3.py "Y:\Bz\MrhOp\meetings\2026\2026_05_20 12-30-36.mp3" --model large --device cuda 


## need to output a current timestamp before model.transcribe() call 


## need to output an actual chosen device


## UserWarning: Failed to launch Triton kernels, likely due to missing CUDA toolkit; falling back to a slower DTW implementation...

- Install the CUDA Toolkit: Ensure you have a compatible version of the NVIDIA CUDA Toolkit installed locally (typically version 11.4 or higher for Triton support).
- Verify System PATH: Add the CUDA bin and libnvvp directories to your system environment variables. This allows Python to find the necessary nvcc compiler.
- Install Triton (Windows Users): Since Triton does not officially support Windows natively, you may need a community-provided wheel. You can find pre-built wheels on platforms like Hugging Face.


## if that is possible to use DirectML with this app to improve performance

Seems yes...


## Error during transcription: '>=' not supported between instances of 'torch.device' and 'int'


In MP3 tags I see following...
- album: Desktop call recorder | Microsoft Teams
- title: MrhOp Daily Stand Up | Microsoft Teams

```
role: Python developer
task:
  extract from sourece `mp3` file 2 fields - `album` and `title`.
  save both as first 2 lines the output file.
```

## In addition to album, title, device, time need also to add a line with timestamp when MP3 was recorded (take it from MP3 info) and length of record


## Error during transcription: CUDA was requested, but this Python environment does not have CUDA support. Install a CUDA-enabled PyTorch build and verify torch.cuda.is_available() is True.

Your script raises that message in transcribe_mp3.py when torch.cuda.is_available() is False. I checked the current repo venv and it is now using a CPU-only Torch build:

The most likely cause is the recent torch-directml install. In this venv, torch-directml is installed, and Torch is noY:

So the CUDA-enabled Torch that you had before was replaced by a CPU build compatible with DirectML. In practice, that means:

CUDA mode needs a CUDA-enabled PyTorch build
DirectML mode uses torch-directml
Mixing both in the same venv is fragile and often ends with one backend replacing the other

### Yes, please prepare 3 files you mentioned - `requirements-base.txt`, `requirements-cuda.txt`, `requirements-dml.txt`

CUDA check:
```
(.venv-cuda) PS Y:\projects\python\whisper> python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
2.11.0+cu128
12.8
True
```

DML check:
```
(.venv-dml) PS Y:\projects\python\whisper> python -c "import importlib, torch; print(torch.__version__); print(torch.cuda.is_available()); print(importlib.import_module('torch_directml').device())"
2.4.1+cpu
False
privateuseone:0
```

## need to output 2 empty lines at the end of execution

## why every next call to whisper LLM generating different output

The main reasons are:
- Whisper’s default transcription logic can fall back across multiple temperatures. Once it leaves temperature=0, decoding becomes sampling-based, so repeated runs can differ.
- GPU backends like CUDA and DirectML are not perfectly deterministic. Tiny floating-point differences can change token choices, especially around punctuation or uncertain words.
- Different devices can produce different outputs for the same file: cpu, cuda, and dml will not necessarily decode identically.
- Whisper is a speech-to-text model, not really an LLM, and speech decoding is especially sensitive to small numeric differences.

```python
  transcribe_options = {
      "word_timestamps": True,
      "temperature": 0.0,
      "best_of": 1,
      "beam_size": 1,
      }
```



# System Info

> C:\Program Files\...\CUDA\v13.2\bin\nvcc.exe
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2026 NVIDIA Corporation
Built on Thu_Mar_19_22:28:55_Pacific_Daylight_Time_2026
Cuda compilation tools, release 13.2, V13.2.78
Build cuda_13.2.r13.2/compiler.37668154_0
```

## Links

google-of: nvidia cuda toolkit
  https://developer.nvidia.com/cuda-downloads?target_os=Windows



# Run

Created sym-link to folder with meeting recordings...

> junction v00 Y:\Bz\MrhOp\meetings
> 
> pip install -r requirements.txt
>
> python.exe -m pip install --upgrade pip 
>
> .\.venv\scripts\activate.ps1
> 
> py -3.12 -m py_compile transcribe_mp3.py
> 
> python transcribe_mp3.py "v00\2026\2026_01_20 06-00-31:.mp3" --model small
> python transcribe_mp3.py "v00\2026\2026_01_20 06-00-31:.mp3" --model small --device cpu
> python transcribe_mp3.py "v00\2026\2026_01_20 06-00-31:.mp3" --model small --device dml

**Note**:
- whisper models cache = C:\Users\%UserName%\.cache\whisper\large-v3.pt

> python transcribe_mp3.py "C:\Users\%UserName%\AppData\Roaming\Desktop call recorder\Recordings\Desktop call recordings\2026_05_20 07-00-54.mp3" 
> python transcribe_mp3.py "C:\Users\%UserName%\AppData\Roaming\Desktop call recorder\Recordings\Desktop call recordings\2026_05_20 07-00-54.mp3" --model large

> python transcribe_mp3.py "Y:\Bz\MrhOp\meetings\2026\2026_05_20 12-30-36.mp3" --model large


## small files for test cases

> py -3.12 transcribe_mp3.py "v00\2026_01_20 06-00-31:.mp3" --model medium 



## Console Output Example

on Core i15-13xxx:
```
(.venv) PS Y:\projects\python\whisper> python transcribe_mp3.py "Y:\Bz\MrhOp\meetings\2026\2026_05_20 12-30-36.mp3" --model large
Transcription started at: 2026-05-20T14:19:08.039062+03:00
Actual device: cuda:0 (NVIDIA GeForce RTX 3060)
Y:\projects\python\whisper\.venv\Lib\site-packages\whisper\timing.py:42: UserWarning: Failed to launch Triton kernels, likely due to missing CUDA toolkit; falling back to a slower median kernel implementation...
  warnings.warn(
Y:\projects\python\whisper\.venv\Lib\site-packages\whisper\timing.py:146: UserWarning: Failed to launch Triton kernels, likely due to missing CUDA toolkit; falling back to a slower DTW implementation...
  warnings.warn(
Y:\projects\python\whisper\.venv\Lib\site-packages\whisper\timing.py:42: UserWarning: Failed to launch Triton kernels, likely due to missing CUDA toolkit; falling back to a slower median kernel implementation...
  warnings.warn(
Y:\projects\python\whisper\.venv\Lib\site-packages\whisper\timing.py:146: UserWarning: Failed to launch Triton kernels, likely due to missing CUDA toolkit; falling back to a slower DTW implementation...
  warnings.warn(
Transcription finished at: 2026-05-20T14:27:08.325748+03:00
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_05_20 12-30-36.large.txt
Device used: cuda:0 (NVIDIA GeForce RTX 3060)
Transcription time: 480.29 seconds
```

on laptop (with DML):
```
(.venv) PS C:\sbx\dbo\dbo-whisper\whisper> python transcribe_mp3.py "v00\2026_05_20 07-00-54.mp3" --model medium --device dml
Transcription started at: 2026-05-20T15:53:33.651167+03:00
Actual device: dml (privateuseone:0)
DirectML compatibility mode: word_timestamps disabled.
Transcription finished at: 2026-05-20T16:23:45.236174+03:00
Transcript saved to: C:\Users\%UserName%\AppData\Roaming\Desktop call recorder\Recordings\Desktop call recordings\2026_05_20 07-00-54.medium.txt
Device used: dml (privateuseone:0)
Transcription time: 1811.61 seconds
(.venv) PS C:\sbx\dbo\dbo-whisper\whisper> 
```

also..
```
[...]
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.large.txt
Device used: cuda:0 (NVIDIA GeForce RTX 3060)
Transcription time: 765.81 seconds
[...]
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.txt
Device used: cuda:0 (NVIDIA GeForce RTX 3060)
Transcription time: 213.99 seconds
[...]
Transcription finished at: 2026-05-21T11:14:13.810561+03:00
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.txt
Device used: cpu
Transcription time: 526.59 seconds
[...]
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.txt
Device used: dml (privateuseone:0)
Transcription time: 456.01 seconds
```

also...
```
(.venv) PS Y:\projects\python\whisper> python transcribe_mp3.py "v00\2026\2026_01_20 06-00-31:.mp3" --model small --device dml
Error during transcription: DirectML was requested, but torch-directml is not installed. Run: python -m pip install torch-directml
[...]
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.medium.txt
Device used: dml (privateuseone:0)
Transcription time: 377.61 seconds
[...]
Device used: dml (privateuseone:0)
Transcription time: 87.84 seconds
```



# Test Results

## Default Temperature (random)

### Device used: cuda:0 (NVIDIA GeForce RTX 3060)

#### Model: SMALL
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.cuda-tc1.txt
- Transcription time: 107.60 seconds
- Transcription time: 109.32 seconds
- Transcription time: 111.07 seconds
average = 109

#### Model: MEDIUM
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.medium.cuda-tc1.txt
- Transcription time: 302.15 seconds
- Transcription time: 339.49 seconds
- Transcription time: 254.59 seconds
average = 298

#### Model: LARGE
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.large.cuda-tc1.txt
- Transcription time: 702.80 seconds
- Transcription time: 560.42 seconds
- Transcription time: 626.91 seconds
average = 629


### Device: dml (privateuseone:0)

#### Model: SMALL
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.dml-tc1.txt
- Transcription time: 205.04 seconds
- Transcription time: 415.63 seconds
- Transcription time: 42.13 seconds  <- failure, just empty file!

#### Model: MEDIUM
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.large.cuda-tc1.txt
- Transcription time: 520.44 seconds
- Transcription time: 531.13 seconds

(aborted test)


#### Model: LARGE


## Temperature = 0 (maximum deterministic)

### Device used: cuda:0 (NVIDIA GeForce RTX 3060)

#### Model: SMALL

GPU Memory usage: ~4316 MB
GPU Load: ~20%
GPU temperature: avg=55^C / hotSpot=70^C

Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.small.cuda-tc1.txt
- Transcription time: 306.83 seconds
- Transcription time: 197.18 seconds
- Transcription time: 175.68 seconds

(results very bad! lot of dummy/trash characters in output file)


#### Model: MEDIUM
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.medium.cuda-tc1.txt
- Transcription time: 176.61 seconds
- Transcription time: 172.82 seconds
- Transcription time: 175.68 seconds

(result good and stable - all 3 cases produce the same file, recognized text looks correctly)


#### Model: LARGE
Transcript saved to: Y:\Bz\MrhOp\meetings\2026\2026_01_20 06-00-31:.large.cuda-tc1.txt
- Transcription time: 520.44 seconds
- Transcription time: 531.13 seconds
- Transcription time: 1086.19 seconds

(result stable by very bad - after ~60 phrases transcriber fall into weird cycle)



# Assistant Prompts 

How to ask AI to generate summary on transcript text:

## RU

```
Ты мой профессиональный AI-ассистент по анализу стенограмм. Вот текст митинга (совещания). 
Сделай из него структурированное саммари. Пожалуйста, используй маркированные списки 
и выдели следующие блоки:
Главная тема и цель встречи: (В 1-2 предложениях).
Основные вопросы и тезисы: (Кратко, кто и о чем говорил).
Принятые решения: (К чему пришли, какие договоренности зафиксированы).
Список задач (Action Items): (Формат: Задача — Ответственный — Срок выполнения, если это упоминалось).
Разногласия / Открытые вопросы: (Что осталось нерешенным).
```

## EN

```
You're my professional AI assistant for transcript analysis. Here's the meeting transcript.
Create a structured summary from it. Please use bullet points
and highlight the following sections:
Main Topic and Purpose of the Meeting: (In 1-2 sentences).
Key Issues and Points: (Briefly, who discussed what).
Decisions Made: (What was reached, what agreements were recorded).
Action Items: (Format: Task - Responsible Person - Deadline, if mentioned).
Disagreements/Open Issues: (What remains unresolved).
```
