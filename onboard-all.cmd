@echo off
rem Refresh every host adapter, validate, then track untracked projects.
rem Existing tracking is reported and preserved. Use --dry-run to preview.
setlocal
python "%~dp0scripts\onboard-all.py" %*
exit /b %errorlevel%
