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

set PYTHON=C:\Users\gelum\AppData\Local\Programs\Python\Python313\python.exe

REM Check if game is running
tasklist /FI "IMAGENAME eq CrimsonDesert.exe" 2>NUL | find /I "CrimsonDesert.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo [!] CrimsonDesert.exe not running. Start the game first.
    echo     Press any key to continue anyway...
    pause >NUL
)

REM Start HTTP server for the map
echo [1/3] Starting map server on http://localhost:8080 ...
start "Map Server" /min %PYTHON% -m http.server 8080 --directory "%~dp0"
timeout /t 1 >NUL

REM Start CD Companion (position tracking) - needs admin
echo [2/3] Starting position tracker (needs admin)...
powershell -Command "Start-Process '%PYTHON%' -ArgumentList '%~dp0tools\start_companion.py' -Verb RunAs -WindowStyle Minimized"
timeout /t 3 >NUL

REM Start Gold Scanner - needs admin
echo [3/3] Starting gold bar scanner (needs admin)...
powershell -Command "Start-Process '%PYTHON%' -ArgumentList '%~dp0tools\gold_scanner.py' -Verb RunAs -WindowStyle Minimized"
timeout /t 2 >NUL

REM Open map in browser
echo.
echo Opening map in browser...
start "" "http://localhost:8080"

echo.
echo ========================================
echo  All services running!
echo  Map:       http://localhost:8080
echo  Position:  ws://localhost:7891
echo  Gold scan: ws://localhost:7892
echo ========================================
echo.
echo Close this window to stop the map server.
echo (Position tracker and gold scanner run separately as admin)
echo.

pause >NUL
taskkill /FI "WINDOWTITLE eq Map Server" /F >NUL 2>&1
