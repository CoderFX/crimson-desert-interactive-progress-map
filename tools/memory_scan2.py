"""
Crimson Desert Memory Scanner v2
Scans for game data structures by looking for:
1. Korean text strings (game UI is localized)
2. Float pairs that match known marker coordinates
3. Internal file paths from the game engine
"""

import ctypes
import ctypes.wintypes as wt
import struct
import sys
import subprocess
import json

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000

kernel32 = ctypes.windll.kernel32

class MBI64(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_uint64),
        ("AllocationBase", ctypes.c_uint64),
        ("AllocationProtect", wt.DWORD),
        ("__alignment1", wt.DWORD),
        ("RegionSize", ctypes.c_uint64),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
        ("__alignment2", wt.DWORD),
    ]

def get_pid():
    r = subprocess.run(['powershell.exe', '-Command',
        "Get-Process -Name 'CrimsonDesert' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True)
    return int(r.stdout.strip()) if r.stdout.strip() else None

def read_regions(pid, callback, max_mb=10000):
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        print("Failed to open process. Run as admin?")
        return

    mbi = MBI64()
    address = 0
    total_mb = 0

    while total_mb < max_mb:
        ret = kernel32.VirtualQueryEx(handle, ctypes.c_uint64(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if ret == 0:
            break

        if mbi.State == MEM_COMMIT and (mbi.Protect & 0xFF) in {0x02, 0x04, 0x06, 0x20, 0x40, 0x60}:
            size = min(mbi.RegionSize, 64 * 1024 * 1024)
            buf = ctypes.create_string_buffer(size)
            br = ctypes.c_size_t()
            if kernel32.ReadProcessMemory(handle, ctypes.c_uint64(mbi.BaseAddress), buf, size, ctypes.byref(br)):
                data = buf.raw[:br.value]
                total_mb += br.value / (1024*1024)
                callback(data, mbi.BaseAddress)

        address = mbi.BaseAddress + mbi.RegionSize
        if address <= mbi.BaseAddress:
            break

    kernel32.CloseHandle(handle)
    print(f"Scanned {total_mb:.0f} MB")

if __name__ == '__main__':
    pid = get_pid()
    if not pid:
        print("Game not running")
        sys.exit(1)
    print(f"PID: {pid}")

    # Strategy 1: Search for coordinate pairs that match known marker locations
    # Our markers use lat/lng like 0.62122330990415, -0.84049726123084
    # In memory these might be stored as floats or doubles
    # Let's search for a few known coordinates as float32 pairs
    known_coords = [
        (0.6695, -0.8459),   # Alpha Wolf Helm
        (0.6212, -0.8405),   # Hernand Castle
        (0.7616, -0.7377),   # Spire of Insight approx
    ]

    # Pack as float32 pairs to search
    coord_patterns = []
    for lat, lng in known_coords:
        # Try both orderings: (lat, lng) and (lng, lat)
        coord_patterns.append((struct.pack('<ff', lat, lng), f"({lat},{lng})"))
        coord_patterns.append((struct.pack('<ff', lng, lat), f"({lng},{lat})"))
        # Also try x,y with 0,z or z,0 padding
        coord_patterns.append((struct.pack('<ff', lat, lng), f"f32({lat},{lng})"))

    # Strategy 2: Search for level/scene path strings (game engine internal IDs)
    # These appear in logs and would be used to track which content is loaded/completed
    scene_strings = [
        b"challenge_sealed_artifact",
        b"mission_hernandcastle",
        b"mission_greymanecamp",
        b"graymanecampequipment",
        b"vein_minerals",
        b"treasure_chest",
        b"sector_",
        b"quest_data",
        b"player_inventory",
        b"save_data",
        b"game_progress",
        b"completion",
        b"collected_items",
        b"discovered",
        b"unlocked",
        b"explored",
    ]

    # Strategy 3: Look for arrays of small integers (item IDs)
    # If the game tracks collected items as an array of uint32 IDs

    coord_hits = {}
    string_hits = {}
    id_array_candidates = []

    def scan_callback(data, base_addr):
        # Search for coordinate patterns
        for pattern, name in coord_patterns:
            pos = 0
            while True:
                pos = data.find(pattern, pos)
                if pos == -1:
                    break
                addr = base_addr + pos
                if name not in coord_hits:
                    coord_hits[name] = []
                coord_hits[name].append(hex(addr))
                # Read surrounding context
                ctx_start = max(0, pos - 16)
                ctx_end = min(len(data), pos + 32)
                ctx = data[ctx_start:ctx_end]
                # Try to read as a series of floats
                floats = []
                for i in range(0, min(48, len(ctx) - 3), 4):
                    f = struct.unpack('<f', ctx[i:i+4])[0]
                    if -10 < f < 10 and f != 0:
                        floats.append(round(f, 6))
                if floats:
                    coord_hits[name].append(f"  context_floats: {floats}")
                pos += len(pattern)

        # Search for engine strings
        for s in scene_strings:
            pos = data.find(s)
            if pos != -1 and s not in string_hits:
                addr = base_addr + pos
                ctx = data[max(0,pos-20):min(len(data), pos+80)]
                try:
                    readable = ctx.decode('utf-8', errors='replace')
                except:
                    readable = str(ctx[:60])
                string_hits[s.decode()] = {'addr': hex(addr), 'context': readable[:120]}
                print(f"  STRING: '{s.decode()}' at {hex(addr)}")

    print("Scanning for coordinates and engine strings...")
    read_regions(pid, scan_callback)

    print(f"\n=== COORDINATE HITS: {len(coord_hits)} ===")
    for name, addrs in coord_hits.items():
        print(f"  {name}: {len([a for a in addrs if a.startswith('0x')])} locations")
        for a in addrs[:6]:
            print(f"    {a}")

    print(f"\n=== STRING HITS: {len(string_hits)} ===")
    for name, info in string_hits.items():
        print(f"  {name}: {info['addr']}")
        print(f"    context: {info['context'][:100]}")

    # Save all results
    with open('memory_scan2_results.json', 'w') as f:
        json.dump({'coordinates': coord_hits, 'strings': {k: v['addr'] for k,v in string_hits.items()}}, f, indent=2)
    print("\nSaved to memory_scan2_results.json")
