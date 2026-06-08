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
timeout /t 1 >NUL

REM Try to find Python
set PYTHON=
for %%P in (python.exe python3.exe) do (
    where %%P >NUL 2>&1 && set "PYTHON=%%P" && goto :found
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PYTHON=%%D\python.exe" && goto :found
)
echo.
echo  Python not found!
echo.
echo  Download it from: https://www.python.org/downloads/
echo  IMPORTANT: Check "Add python.exe to PATH" during install.
echo.
pause
exit /b 1

:found
echo Using Python: %PYTHON%
echo.

echo [1/2] Starting map server on http://localhost:8080 ...
start "Map Server" /min /d "%~dp0" "%PYTHON%" -m http.server 8080
timeout /t 2 >NUL

REM Start position tracker if game is running
tasklist /FI "IMAGENAME eq CrimsonDesert.exe" 2>NUL | find /I "CrimsonDesert.exe" >NUL
if %ERRORLEVEL% EQU 0 (
    echo [2/2] Starting position tracker (needs admin)...
    powershell -Command "Start-Process '%PYTHON%' -ArgumentList '%~dp0tools\start_companion.py' -Verb RunAs -WindowStyle Minimized"
    timeout /t 3 >NUL
) else (
    echo [2/2] Game not running - position tracker skipped
)

echo Opening map in browser...
start "" "http://localhost:8080"

echo.
echo ========================================
echo  Map running at http://localhost:8080
echo ========================================
echo.
echo Close this window to stop the map server.
echo.

pause >NUL
taskkill /FI "WINDOWTITLE eq Map Server" /F >NUL 2>&1
