@echo off
setlocal
cd /d "%~dp0"
if not exist verification\windows mkdir verification\windows
py -m unittest discover -s tests -v > verification\windows\unit_tests.txt 2>&1
if errorlevel 1 (type verification\windows\unit_tests.txt & pause & exit /b 1)
type verification\windows\unit_tests.txt
py src\analyze_curve.py --self-check > verification\windows\calculation_self_check.txt 2>&1
if errorlevel 1 (type verification\windows\calculation_self_check.txt & pause & exit /b 1)
type verification\windows\calculation_self_check.txt
echo PASS: Python tests completed. Browser checks still need the checklist.
pause
