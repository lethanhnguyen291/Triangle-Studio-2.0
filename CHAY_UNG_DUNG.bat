@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
call "%~dp0TIM_PYTHON.bat"
if errorlevel 1 goto no_python
for %%P in ("%TS_PYTHON%") do start "" "%%~dpPpythonw.exe" "%~dp0main.py"
if errorlevel 1 goto failed
exit /b 0

:no_python
echo Khong tim thay Python hoat dong. Hay chay CAI_DAT.bat.
pause
exit /b 1

:failed
echo.
echo Ung dung gap loi. Hay chup thong bao o tren de kiem tra.
pause
exit /b 1
