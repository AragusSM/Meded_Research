@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo MedVale RAG Lab has not been set up yet.
  echo Running the one-time setup now...
  call setup_windows.bat
  if errorlevel 1 exit /b 1
)

echo Starting MedVale RAG Lab...
echo Keep this window open. Press Ctrl+C here when you want to stop.
.venv\Scripts\python.exe run_app.py
