@echo off
REM If running inside MSYS2/Git Bash, relaunch in cmd.exe
if defined MSYSTEM (
    cmd.exe /c "%~f0" %*
    exit /b
)

title Crimson Desert Map Launcher
cd /d "%~dp0"

echo ========================================
echo  Crimson Desert Interactive Progress Map
echo ========================================
echo.

REM Kill any old map servers on port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080.*LISTENING"') do taskkill /F /PID %%a >NUL 2>&1

REM Find Python
set PYTHON=
where python >NUL 2>&1 && set PYTHON=python&& goto :found
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"&& goto :found
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"&& goto :found
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"&& goto :found
if exist "C:\Python313\python.exe" set "PYTHON=C:\Python313\python.exe"&& goto :found
if exist "C:\Python312\python.exe" set "PYTHON=C:\Python312\python.exe"&& goto :found
echo [ERROR] Python not found. Install from https://www.python.org/downloads/
echo         Check "Add python.exe to PATH" during install.
pause
exit /b 1

:found
echo Using: %PYTHON%
echo.

REM Start map server
echo [1/2] Starting map server...
start "Map Server" /min "%PYTHON%" -m http.server 8080 --bind 127.0.0.1 --directory "%~dp0."
timeout /t 2 >NUL

REM Start position tracker if game is running and CD Companion is available
tasklist /FI "IMAGENAME eq CrimsonDesert.exe" 2>NUL | find /I "CrimsonDesert.exe" >NUL
if %ERRORLEVEL% EQU 0 (
    if exist "%~dp0tools\start_companion.py" (
        echo [2/2] Starting position tracker...
        powershell -Command "Start-Process \"%PYTHON%\" -ArgumentList \"\"\"%~dp0tools\start_companion.py\"\"\" -Verb RunAs -WindowStyle Minimized" 2>NUL
        timeout /t 3 >NUL
    ) else (
        echo [2/2] Position tracker not found - skipped
    )
) else (
    echo [2/2] Game not running - position tracker skipped
)

start "" "http://localhost:8080"

echo.
echo ========================================
echo  Map: http://localhost:8080
echo  Close this window to stop.
echo ========================================
pause >NUL
taskkill /FI "WINDOWTITLE eq Map Server" /F >NUL 2>&1
