@echo off
setlocal
cd /d "%~dp0"
py -m streamlit run app.py
if errorlevel 1 echo Command failed. Please copy the error above.
pause
