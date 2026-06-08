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

REM Auto-detect Python
where python >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
) else (
    set PYTHON=python3
)

REM Kill any old map servers on port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080.*LISTENING"') do taskkill /F /PID %%a >NUL 2>&1
timeout /t 1 >NUL

REM Start HTTP server for the map
echo Starting map server on http://localhost:8080 ...
start "Map Server" /min /d "%~dp0" %PYTHON% -m http.server 8080
timeout /t 2 >NUL

REM Open map in browser
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
