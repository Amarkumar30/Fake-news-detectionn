@echo off
setlocal EnableExtensions EnableDelayedExpansion

where python >nul 2>nul
if errorlevel 1 (
  echo Python is required but was not found.
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is required but was not found.
  exit /b 1
)

for /f "delims=" %%i in ('python --version 2^>^&1') do echo Python version: %%i
for /f "delims=" %%i in ('node --version') do echo Node version: %%i

dir /b backend\models\*.pkl >nul 2>nul
if errorlevel 1 (
  echo No trained model artifacts found. Running backend\train.py...
  pushd backend
  python train.py --data-dir ..\data
  if errorlevel 1 (
    popd
    exit /b 1
  )
  popd
)

powershell -NoProfile -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$root = '%CD%';" ^
  "$exitCode = 0;" ^
  "$backend = $null;" ^
  "try {" ^
  "  $env:FLASK_ENV = 'development';" ^
  "  $env:FLASK_PORT = '5000';" ^
  "  $backend = Start-Process python -ArgumentList 'app.py' -WorkingDirectory (Join-Path $root 'backend') -PassThru;" ^
  "  Write-Host ('Started Flask backend with PID ' + $backend.Id);" ^
  "  Push-Location (Join-Path $root 'frontend');" ^
  "  npm.cmd run dev;" ^
  "  $exitCode = $LASTEXITCODE;" ^
  "}" ^
  "finally {" ^
  "  Pop-Location -ErrorAction SilentlyContinue;" ^
  "  if ($backend) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }" ^
  "}" ^
  "exit $exitCode"

exit /b %ERRORLEVEL%
