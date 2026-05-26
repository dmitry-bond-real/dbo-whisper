#
# Testing transcriber python app
#

$ErrorActionPreference = 'Stop'

$PythonEnvPath = Join-Path $PSScriptRoot '.venv-cuda'
#$PythonEnvPath = Join-Path $PSScriptRoot '.venv-dml'

$ActivateScript = Join-Path $PythonEnvPath 'Scripts\Activate.ps1'
$PythonExe = Join-Path $PythonEnvPath 'Scripts\python.exe'

#$RecordingsDir = Join-Path $PSScriptRoot 'v00\2025'
#$RecordingsDir = Join-Path $PSScriptRoot 'v00\larchanka'
$RecordingsDir = Join-Path $PSScriptRoot 'v00\last3'

$Model = 'medium'

$Device = 'cuda'
#$Device = 'dml'
#$Device = 'cpu'

$Formatting = 'dot'
$TranscribeOption = 'static'
$Marker = $null
$NoConditionOnPreviousText = $true


if (-not (Test-Path -LiteralPath $ActivateScript)) {
    throw "Python activation script was not found: $ActivateScript"
}

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable was not found: $PythonExe"
}

if (-not (Test-Path -LiteralPath $RecordingsDir -PathType Container)) {
    throw "Recordings directory was not found: $RecordingsDir"
}

& $ActivateScript

Write-Host "Activated environment: $PythonEnvPath"
Write-Host 'Compiling transcribe_mp3.py...'

& $PythonExe -m py_compile (Join-Path $PSScriptRoot 'transcribe_mp3.py')

if ($LASTEXITCODE -ne 0) {
    throw 'Python compilation failed.'
}

$commonArgs = @(
    '--model', $Model
    , '--device', $Device
    , '--formatting', $Formatting
    , '--transcribe-option', $TranscribeOption
    #, '--language', 'ru'
)

if ($NoConditionOnPreviousText) {
    $commonArgs += '--no-condition-on-previous-text'
}

$sourceFiles = Get-ChildItem -LiteralPath $RecordingsDir -Filter '*.mp3' -File | Sort-Object Name
$totalFiles = $sourceFiles.Count
$processedFiles = 0
$skippedFiles = 0

if ($totalFiles -eq 0) {
    Write-Host "No MP3 files found in: $RecordingsDir"
    return
}

foreach ($file in $sourceFiles) {
    $processedFiles++

    $outputNameParts = @($file.BaseName, $Model)
    if ($Marker) {
        $outputNameParts += $Marker
    }

    $outputFile = Join-Path $file.DirectoryName (('.' + ($outputNameParts -join '.')).TrimStart('.') + '.txt')

    if (Test-Path -LiteralPath $outputFile -PathType Leaf) {
        $skippedFiles++
        Write-Host "--- Skipping file ${processedFiles} of ${totalFiles}: [ $($file.Name) ] -> result already exists: $outputFile"
        continue
    }

    $msg = "--- Transcribing file ${processedFiles} of ${totalFiles}: [ $($file.Name) ] ..."
    $Host.UI.RawUI.WindowTitle = $msg
    Write-Host $msg

    $commandArgs = @(
        (Join-Path $PSScriptRoot 'transcribe_mp3.py'),
        $file.FullName
    ) + $commonArgs

    $Marker = "tc1"
    if ($Marker) {
        $commandArgs += @('--marker', $Marker)
    }
    & $PythonExe @commandArgs

    $Marker = "tc2"
    if ($Marker) {
        $commandArgs += @('--marker', $Marker)
    }
    & $PythonExe @commandArgs

    $Marker = "tc3"
    if ($Marker) {
        $commandArgs += @('--marker', $Marker)
    }
    & $PythonExe @commandArgs

    if ($LASTEXITCODE -ne 0) {
        throw "Transcription failed for '$($file.Name)' (file $processedFiles of $totalFiles)."
    }
}

$msg = "All transcription runs completed. Checked $processedFiles of $totalFiles files, skipped $skippedFiles existing results."
$Host.UI.RawUI.WindowTitle = $msg
Write-Host $msg
