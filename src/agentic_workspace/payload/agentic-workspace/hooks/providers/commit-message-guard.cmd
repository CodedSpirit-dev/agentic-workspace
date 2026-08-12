@echo off
setlocal
set "GUARD_SCRIPT=%~dp0commit-message-guard.py"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 goto run_py

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 goto run_python

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 goto run_python3

echo ERROR: the commit policy guard requires Python 3.11 or newer 1>&2
exit /b 127

:run_py
py -3 "%GUARD_SCRIPT%"
exit /b %ERRORLEVEL%

:run_python
python "%GUARD_SCRIPT%"
exit /b %ERRORLEVEL%

:run_python3
python3 "%GUARD_SCRIPT%"
exit /b %ERRORLEVEL%
