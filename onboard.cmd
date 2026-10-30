@echo off
setlocal
if /I "%~1"=="--all" (
  python "%~dp0scripts\onboard-all.py" %*
) else (
  python "%~dp0scripts\onboard.py" %*
)
exit /b %errorlevel%
