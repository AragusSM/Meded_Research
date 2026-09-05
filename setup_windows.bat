@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto no_python
  set "PYTHON_CMD=python"
)

echo Creating the MedVale RAG Lab environment...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto failed

echo Installing required packages...
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo.
echo Setup complete. Double-click run_windows.bat to start MedVale RAG Lab.
pause
exit /b 0

:no_python
echo Python was not found. Install Python 3.10 or newer from python.org.
echo During installation, select "Add Python to PATH".
pause
exit /b 1

:failed
echo.
echo Setup did not finish. Review the error above, then try again.
pause
exit /b 1
