@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Hay chay CAI_DAT.bat truoc.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean TriangleStudio.spec
if errorlevel 1 goto failed
echo.
echo Da tao dist\TriangleStudio_2.0.exe
echo May khac co the chay file EXE nay ma khong can cai Python.
pause
exit /b 0
:failed
echo Tao EXE chua thanh cong. Xem thong bao loi o tren.
pause
exit /b 1
