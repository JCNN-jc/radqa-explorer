@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements_app.txt
if errorlevel 1 echo Command failed. Please copy the error above.
pause
