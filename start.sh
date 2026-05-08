#!/bin/bash
# Crimson Desert Interactive Progress Map Launcher (MSYS2/bash version)
cd "$(dirname "$0")"

PYTHON="/c/Users/gelum/AppData/Local/Programs/Python/Python313/python.exe"

echo "========================================"
echo " Crimson Desert Interactive Progress Map"
echo "========================================"
echo ""

# Check if game is running
if ! powershell.exe -Command "Get-Process -Name CrimsonDesert -ErrorAction SilentlyContinue" 2>/dev/null | grep -q CrimsonDesert; then
    echo "[!] CrimsonDesert.exe not running. Start the game first."
    read -p "    Press Enter to continue anyway..."
fi

# Start HTTP server
echo "[1/3] Starting map server on http://localhost:8080 ..."
"$PYTHON" -m http.server 8080 --directory "$(pwd)" &
MAP_PID=$!
sleep 1

# Start CD Companion (needs admin)
echo "[2/3] Starting position tracker (needs admin)..."
powershell.exe -Command "Start-Process '$PYTHON' -ArgumentList '$(cygpath -w "$(pwd)/tools/start_companion.py")' -Verb RunAs -WindowStyle Minimized" 2>/dev/null
sleep 3

# Start Gold Scanner (needs admin)
echo "[3/3] Starting gold bar scanner (needs admin)..."
powershell.exe -Command "Start-Process '$PYTHON' -ArgumentList '$(cygpath -w "$(pwd)/tools/gold_scanner.py")' -Verb RunAs -WindowStyle Minimized" 2>/dev/null
sleep 2

# Open browser
echo ""
echo "Opening map in browser..."
cmd.exe /c start "" "http://localhost:8080" 2>/dev/null

echo ""
echo "========================================"
echo " All services running!"
echo " Map:       http://localhost:8080"
echo " Position:  ws://localhost:7891"
echo " Gold scan: ws://localhost:7892"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop the map server."
echo "(Position tracker and gold scanner run separately as admin)"
echo ""

wait $MAP_PID
