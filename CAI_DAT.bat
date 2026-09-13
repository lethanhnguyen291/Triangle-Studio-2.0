@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
echo === Triangle Studio 2.0 - Cai dat da sua loi Python Launcher ===
if not exist ".venv\Scripts\python.exe" goto find_python
".venv\Scripts\python.exe" -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 goto install_packages

:find_python
call "%~dp0TIM_PYTHON.bat"
if errorlevel 1 goto no_python
echo Da tim thay Python hoat dong:
echo "%TS_PYTHON%"
rem Preserve an incomplete or broken environment before creating a new one.
if not exist ".venv" goto create_env
set "TS_BACKUP=.venv.backup-%RANDOM%-%RANDOM%"
move ".venv" "%TS_BACKUP%" >nul
if errorlevel 1 goto failed
echo Moi truong cu duoc giu tai "%TS_BACKUP%".

:create_env
"%TS_PYTHON%" -m venv .venv
if errorlevel 1 goto failed

:install_packages
".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m ensurepip --upgrade
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Da cai xong. Mo CHAY_UNG_DUNG.bat de su dung.
pause
exit /b 0

:no_python
echo.
echo Chua tim thay Python 3.10+ co Tkinter dang hoat dong.
echo Python Launcher co the con luu duong dan cua ban Python da bi xoa.
echo.
echo Danh sach Python Launcher dang ghi nhan:
py -0p 2>nul
echo.
echo Cac lenh Python tren PATH:
where.exe python.exe 2>nul
echo.
echo Hay chup man hinh nay de kiem tra, hoac cai/sua Python tu python.org.
echo Khi cai, chon Tcl/Tk va Add python.exe to PATH.
echo Xem file SUA_LOI_PYTHON.txt neu ban biet duong dan python.exe.
pause
exit /b 1

:failed
echo.
echo Cai dat chua thanh cong. Xem loi o tren.
echo Neu loi tai thu vien, kiem tra ket noi Internet va quyen ghi thu muc.
pause
exit /b 1
