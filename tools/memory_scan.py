"""
Crimson Desert Memory Scanner
Scans the game process memory for known item/location strings
to identify data structures that track collected items.

Usage: python tools/memory_scan.py
Requires: Windows, game running, admin privileges may be needed
"""

import ctypes
import ctypes.wintypes as wt
import struct
import sys
import json
import os

# Windows API constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_READABLE = {0x02, 0x04, 0x06, 0x20, 0x40, 0x60, 0x80}  # PAGE_READONLY, READWRITE, EXECUTE_READ, etc.

kernel32 = ctypes.windll.kernel32

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
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

def get_pid_by_name(name):
    """Find process ID by name"""
    import subprocess
    result = subprocess.run(
        ['powershell.exe', '-Command',
         f"Get-Process -Name '{name}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    pids = result.stdout.strip().split('\n')
    return int(pids[0]) if pids and pids[0].strip() else None

def scan_memory(pid, search_strings, max_regions=5000):
    """Scan process memory for given strings, return addresses where found"""
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        print(f"Failed to open process {pid}. Try running as administrator.")
        return {}

    results = {}
    mbi = MEMORY_BASIC_INFORMATION64()
    address = 0
    regions_scanned = 0
    bytes_scanned = 0

    # Encode search strings
    search_bytes = {}
    for s in search_strings:
        # Search for both UTF-8 and UTF-16LE encodings
        search_bytes[s] = [s.encode('utf-8'), s.encode('utf-16-le')]

    print(f"Scanning PID {pid} for {len(search_strings)} strings...")

    while regions_scanned < max_regions:
        ret = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if ret == 0:
            break

        # Only scan committed, readable memory
        if mbi.State == MEM_COMMIT and (mbi.Protect & 0xFF) in PAGE_READABLE:
            size = min(mbi.RegionSize, 100 * 1024 * 1024)  # Cap at 100MB per region
            buf = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            if kernel32.ReadProcessMemory(handle, ctypes.c_void_p(mbi.BaseAddress), buf, size, ctypes.byref(bytes_read)):
                data = buf.raw[:bytes_read.value]
                bytes_scanned += bytes_read.value

                for name, encodings in search_bytes.items():
                    if name in results:
                        continue  # Already found
                    for enc in encodings:
                        pos = data.find(enc)
                        if pos != -1:
                            addr = mbi.BaseAddress + pos
                            encoding_type = 'utf16' if len(enc) > len(name) else 'utf8'
                            results[name] = {
                                'address': hex(addr),
                                'region_base': hex(mbi.BaseAddress),
                                'offset_in_region': pos,
                                'encoding': encoding_type,
                                'region_size': mbi.RegionSize,
                                'protect': hex(mbi.Protect)
                            }
                            # Print context around the match
                            ctx_start = max(0, pos - 32)
                            ctx_end = min(len(data), pos + len(enc) + 64)
                            context = data[ctx_start:ctx_end]
                            print(f"  FOUND '{name}' at {hex(addr)} ({encoding_type})")
                            break

            regions_scanned += 1
            if regions_scanned % 500 == 0:
                print(f"  ... scanned {regions_scanned} regions, {bytes_scanned // (1024*1024)} MB, found {len(results)}/{len(search_strings)}")

        # Move to next region
        address = mbi.BaseAddress + mbi.RegionSize
        if address <= mbi.BaseAddress:  # Overflow protection
            break

    kernel32.CloseHandle(handle)
    print(f"Done: scanned {regions_scanned} regions, {bytes_scanned // (1024*1024)} MB total")
    return results


def scan_region_context(pid, address_hex, size=4096):
    """Read memory around a specific address and dump context"""
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        return None

    address = int(address_hex, 16)
    start = max(0, address - size // 2)
    buf = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()

    if kernel32.ReadProcessMemory(handle, ctypes.c_void_p(start), buf, size, ctypes.byref(bytes_read)):
        kernel32.CloseHandle(handle)
        return buf.raw[:bytes_read.value]

    kernel32.CloseHandle(handle)
    return None


if __name__ == '__main__':
    pid = get_pid_by_name('CrimsonDesert')
    if not pid:
        print("CrimsonDesert process not found. Is the game running?")
        sys.exit(1)

    print(f"Found CrimsonDesert at PID {pid}")

    # Search for known item/location names that the player would collect
    # Mix of unique items, common items, and quest names
    test_strings = [
        # Unique items (if found in memory, player likely has them)
        "Alpha Wolf Helm",
        "Helm of Ignition",
        "Spire of Insight",
        "Ancient Tablet",
        "Hernand Castle",
        # Quest names
        "Black Witch",
        "The Witch of Wisdom",
        # Internal identifiers from game files
        "sealed_artifact",
        "treasure_chest",
        "greymane",
        "hernandcastle",
        # Common strings that should definitely be in memory
        "Stronghold",
        "Treasure Chest",
        "inventory",
        "quest_complete",
        "item_collected",
        "found_item",
        "pickup",
    ]

    results = scan_memory(pid, test_strings)

    print(f"\n=== RESULTS: {len(results)}/{len(test_strings)} strings found ===")
    for name, info in sorted(results.items(), key=lambda x: x[1]['address']):
        print(f"  {name}: addr={info['address']} enc={info['encoding']} protect={info['protect']}")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), '..', 'memory_scan_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    # If we found strings, let's examine the memory around them for data structures
    if results:
        print("\n=== CONTEXT ANALYSIS ===")
        for name, info in list(results.items())[:5]:
            print(f"\n--- Context around '{name}' at {info['address']} ---")
            ctx = scan_region_context(pid, info['address'], 512)
            if ctx:
                # Look for nearby strings (other item names, counters, etc.)
                try:
                    # Try to find nearby readable strings
                    for encoding in ['utf-8', 'utf-16-le']:
                        decoded = ctx.decode(encoding, errors='replace')
                        # Filter to printable segments
                        segments = []
                        current = []
                        for ch in decoded:
                            if ch.isprintable() and ch != '\ufffd':
                                current.append(ch)
                            else:
                                if len(current) >= 4:
                                    segments.append(''.join(current))
                                current = []
                        if len(current) >= 4:
                            segments.append(''.join(current))
                        if segments:
                            print(f"  Nearby strings ({encoding}): {segments[:10]}")
                except:
                    pass
