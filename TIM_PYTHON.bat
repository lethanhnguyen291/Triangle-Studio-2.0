@echo off
rem Called from another BAT with SETLOCAL. Returns TS_PYTHON as an absolute path.
set "TS_PYTHON="
if defined TRIANGLE_PYTHON call :try_path "%TRIANGLE_PYTHON%"
call :try_path "%~dp0.venv\Scripts\python.exe"
for /f "delims=" %%P in ('where.exe python.exe 2^>nul') do call :try_path "%%P"
for /f "delims=" %%P in ('where.exe python3.exe 2^>nul') do call :try_path "%%P"
if defined TS_PYTHON exit /b 0
rem Listing runtimes does not execute the broken default runtime.
for /f "tokens=1,*" %%A in ('py -0p 2^>nul') do call :launcher_line "%%B"
if defined TS_PYTHON exit /b 0
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*" "%LOCALAPPDATA%\Python\pythoncore-*" "%ProgramFiles%\Python*" "%ProgramFiles(x86)%\Python*" "C:\Python*") do call :try_path "%%~fD\python.exe"
if defined TS_PYTHON exit /b 0
exit /b 1

:launcher_line
if defined TS_PYTHON exit /b 0
set "TS_CANDIDATE=%~1"
set "TS_CANDIDATE=%TS_CANDIDATE:"=%"
for /f "tokens=*" %%P in ("%TS_CANDIDATE%") do set "TS_CANDIDATE=%%P"
if "%TS_CANDIDATE:~0,1%"=="*" set "TS_CANDIDATE=%TS_CANDIDATE:~1%"
for /f "tokens=*" %%P in ("%TS_CANDIDATE%") do call :launcher_candidate "%%P"
exit /b 0

:launcher_candidate
call :try_path "%~1"
rem A stale python3.14t.exe registration may sit next to a working python.exe.
call :try_path "%~dp1python.exe"
exit /b 0

:try_path
if defined TS_PYTHON exit /b 0
if "%~1"=="" exit /b 1
if not exist "%~1" exit /b 1
rem Skip Store shortcut aliases; they can open the Store instead of running Python.
if /i "%~dp1"=="%LOCALAPPDATA%\Microsoft\WindowsApps\" exit /b 1
"%~1" -c "import sys, tkinter, venv; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "TS_PYTHON=%~f1"
exit /b 0
