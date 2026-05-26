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
echo = transcribeOption: %trxOpt%

goto cont1

set model=small
echo = model: %model%
set opts=--model %model% --device %dev% %trxOpt% --formatting dot 
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

set model=medium
echo = model: %model%
set opts=--model %model% --device %dev% %trxOpt% --formatting dot 
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

:cont1
set model=turbo
echo = model: %model%
set opts=--model %model% --device %dev% %trxOpt% --formatting dot 
set msg="%DATE%,%TIME% Test cases with [%model%] model"
echo "----------------------------------------------------------"
echo "--- %msg% "
title %msg%
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc1
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc2
python transcribe_mp3.py %srcFile% %opts% --marker %dev%-tc3

title "%DATE%,%TIME% COMPLETED"
