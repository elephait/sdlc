@echo off
setlocal
python "%~dp0scripts\aicode.py" %*
exit /b %errorlevel%
