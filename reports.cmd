@echo off
rem Show the most recent scorecards, failures, analysis and review reports.
setlocal
python "%~dp0scripts\reports.py" %*
exit /b %errorlevel%
