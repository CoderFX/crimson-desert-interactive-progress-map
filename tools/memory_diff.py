"""
Crimson Desert Differential Memory Scanner
-------------------------------------------
Takes two snapshots of memory regions around known game strings,
diffs them to find what changed when the player collects items / completes quests.

Known anchor addresses (from previous scans):
  'discovered'  at 0x440e603b7bf
  'unlocked'    at 0x440e6215c02
  'explored'    at 0x440e625d141
  'completion'  at 0x440e66ca3fb

Usage:
  python tools/memory_diff.py
  (Run with Windows Python, needs admin privileges)
"""

import ctypes
import ctypes.wintypes as wt
import struct
import sys
import os
import time
import subprocess
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Windows API setup
# ---------------------------------------------------------------------------
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_READABLE = {0x02, 0x04, 0x06, 0x20, 0x40, 0x60, 0x80}

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

# ---------------------------------------------------------------------------
# Known anchor addresses from previous memory scan
# ---------------------------------------------------------------------------
ANCHORS = {
    'discovered':  0x440e603b7bf,
    'unlocked':    0x440e6215c02,
    'explored':    0x440e625d141,
    'completion':  0x440e66ca3fb,
}

# Region sizes: 1MB around each anchor for standard diff,
# plus 10MB around discovered/completion for deep analysis
STANDARD_RADIUS = 512 * 1024       # 512KB each side = 1MB region
DEEP_RADIUS     = 5 * 1024 * 1024  # 5MB each side = 10MB region

DEEP_ANCHORS = {'discovered', 'completion'}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "memory_diff_output"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_pid():
    r = subprocess.run(
        ['powershell.exe', '-Command',
         "Get-Process -Name 'CrimsonDesert' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    pid_str = r.stdout.strip().split('\n')[0].strip()
    return int(pid_str) if pid_str else None


def open_process(pid):
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        err = ctypes.get_last_error()
        print(f"[ERROR] Failed to open process {pid}, error={err}. Run as administrator?")
        sys.exit(1)
    return handle


def read_memory(handle, address, size):
    """Read `size` bytes from `address`. Returns bytes or None."""
    buf = ctypes.create_string_buffer(size)
    br = ctypes.c_size_t()
    ok = kernel32.ReadProcessMemory(
        handle, ctypes.c_uint64(address), buf, size, ctypes.byref(br)
    )
    if ok and br.value > 0:
        return buf.raw[:br.value]
    return None


def read_region_chunked(handle, start, total_size, chunk=1024*1024):
    """Read a large region in chunks, skipping unreadable pages."""
    pieces = []
    offset = 0
    while offset < total_size:
        cs = min(chunk, total_size - offset)
        data = read_memory(handle, start + offset, cs)
        if data:
            pieces.append((offset, data))
        else:
            # Try smaller chunks to recover partial reads
            for sub_off in range(0, cs, 4096):
                sub_sz = min(4096, cs - sub_off)
                sub_data = read_memory(handle, start + offset + sub_off, sub_sz)
                if sub_data:
                    pieces.append((offset + sub_off, sub_data))
        offset += cs
    return pieces


def verify_anchor(handle, name, addr):
    """Check whether the anchor string is still at the expected address."""
    data = read_memory(handle, addr - 32, 128)
    if data is None:
        return False
    needle = name.encode('utf-8')
    return needle in data


def take_snapshot(pid, label):
    """Snapshot all anchor regions. Returns dict {name: (start_addr, bytes)}."""
    handle = open_process(pid)
    snapshot = {}
    verified = 0

    for name, anchor in ANCHORS.items():
        # Verify the anchor string is still there
        ok = verify_anchor(handle, name, anchor)
        status = "OK" if ok else "MISSING (address may have shifted)"
        print(f"  [{label}] Anchor '{name}' at {hex(anchor)}: {status}")
        if ok:
            verified += 1

        # Determine radius
        radius = DEEP_RADIUS if name in DEEP_ANCHORS else STANDARD_RADIUS
        start = anchor - radius
        total = radius * 2

        print(f"  [{label}] Reading {total // (1024*1024)}MB around '{name}' ({hex(start)}..{hex(start+total)})")
        pieces = read_region_chunked(handle, start, total)

        # Reassemble into a contiguous buffer (zero-fill gaps)
        buf = bytearray(total)
        bytes_read = 0
        for off, data in pieces:
            end = min(off + len(data), total)
            buf[off:end] = data[:end - off]
            bytes_read += end - off

        snapshot[name] = (start, bytes(buf))
        print(f"  [{label}] Got {bytes_read // 1024}KB / {total // 1024}KB for '{name}'")

    kernel32.CloseHandle(handle)
    print(f"  [{label}] Verified {verified}/{len(ANCHORS)} anchors\n")
    return snapshot


# ---------------------------------------------------------------------------
# Diff engine
# ---------------------------------------------------------------------------

def diff_snapshots(snap1, snap2):
    """Compare two snapshots. Returns dict of changes per anchor region."""
    all_changes = {}

    for name in snap1:
        if name not in snap2:
            continue
        start1, data1 = snap1[name]
        start2, data2 = snap2[name]
        if start1 != start2:
            print(f"  [WARN] Region base changed for '{name}': {hex(start1)} vs {hex(start2)}")
            continue

        sz = min(len(data1), len(data2))
        changes = []

        # Compare in 4-byte aligned blocks for speed, then byte-level within changed blocks
        block_size = 256
        for blk_off in range(0, sz, block_size):
            blk_end = min(blk_off + block_size, sz)
            if data1[blk_off:blk_end] == data2[blk_off:blk_end]:
                continue
            # Byte-level diff within this block
            for i in range(blk_off, blk_end):
                if data1[i] != data2[i]:
                    changes.append((start1 + i, data1[i], data2[i]))

        all_changes[name] = changes
        print(f"  '{name}': {len(changes)} bytes changed out of {sz} bytes compared")

    return all_changes


def extract_nearby_string(data, offset, radius=64):
    """Try to find a readable ASCII/UTF-8 string near an offset in data."""
    start = max(0, offset - radius)
    end = min(len(data), offset + radius)
    chunk = data[start:end]
    segments = []
    current = []
    for b in chunk:
        if 32 <= b < 127:
            current.append(chr(b))
        else:
            if len(current) >= 4:
                segments.append(''.join(current))
            current = []
    if len(current) >= 4:
        segments.append(''.join(current))
    return segments


def classify_change(addr, old_val, new_val, data1, data2, region_start):
    """Heuristic classification of a single byte change."""
    offset = addr - region_start
    info = {
        'addr': hex(addr),
        'offset': offset,
        'old': old_val,
        'new': new_val,
        'old_hex': f'0x{old_val:02x}',
        'new_hex': f'0x{new_val:02x}',
    }

    # Boolean toggle: 0->1 or 1->0
    if (old_val, new_val) in ((0, 1), (1, 0)):
        info['type'] = 'bool_toggle'

    # Counter increment
    elif new_val == old_val + 1:
        info['type'] = 'counter_increment'

    # Counter decrement
    elif new_val == old_val - 1:
        info['type'] = 'counter_decrement'

    # Bit flip (single bit changed in the byte)
    elif bin(old_val ^ new_val).count('1') == 1:
        bit_pos = (old_val ^ new_val).bit_length() - 1
        info['type'] = f'bitfield_flip_bit{bit_pos}'

    else:
        info['type'] = 'value_change'

    return info


def analyze_changes(changes, snap1, snap2):
    """Detailed analysis of all changes per region."""
    report = {}

    for name, change_list in changes.items():
        if not change_list:
            report[name] = {'total_changes': 0, 'details': []}
            continue

        start, data1 = snap1[name]
        _, data2 = snap2[name]

        details = []
        # Group consecutive changes into clusters
        clusters = []
        current_cluster = [change_list[0]]
        for ch in change_list[1:]:
            if ch[0] - current_cluster[-1][0] <= 16:
                current_cluster.append(ch)
            else:
                clusters.append(current_cluster)
                current_cluster = [ch]
        clusters.append(current_cluster)

        for cluster in clusters:
            cluster_start = cluster[0][0]
            cluster_end = cluster[-1][0]
            cluster_info = {
                'cluster_addr': hex(cluster_start),
                'cluster_size': cluster_end - cluster_start + 1,
                'num_bytes_changed': len(cluster),
                'changes': [],
            }

            # Nearby strings (from snapshot 1 data)
            off = cluster_start - start
            nearby = extract_nearby_string(data1, off)
            if nearby:
                cluster_info['nearby_strings'] = nearby

            for addr, old_v, new_v in cluster:
                ci = classify_change(addr, old_v, new_v, data1, data2, start)
                cluster_info['changes'].append(ci)

            # 4-byte / 8-byte value interpretation for small clusters
            if len(cluster) <= 8:
                for width, fmt_name, fmt in [(4, 'uint32', '<I'), (4, 'int32', '<i'),
                                              (4, 'float32', '<f'),
                                              (8, 'uint64', '<Q'), (8, 'double', '<d')]:
                    off = cluster_start - start
                    aligned = off - (off % width)
                    if aligned >= 0 and aligned + width <= len(data1) and aligned + width <= len(data2):
                        old_wide = struct.unpack(fmt, data1[aligned:aligned+width])[0]
                        new_wide = struct.unpack(fmt, data2[aligned:aligned+width])[0]
                        if old_wide != new_wide:
                            cluster_info[f'{fmt_name}_old'] = old_wide
                            cluster_info[f'{fmt_name}_new'] = new_wide

            details.append(cluster_info)

        report[name] = {
            'total_changes': len(change_list),
            'num_clusters': len(clusters),
            'details': details,
        }

    return report


# ---------------------------------------------------------------------------
# Deep structure analysis (for 10MB regions around discovered/completion)
# ---------------------------------------------------------------------------

def deep_analyze_region(name, start, data):
    """Look for arrays of uint32 IDs, boolean arrays, bitfields, counters."""
    findings = []
    sz = len(data)

    print(f"\n  === Deep analysis of '{name}' region ({sz // (1024*1024)}MB) ===")

    # 1. Boolean arrays: runs of 0x00/0x01 bytes (at least 16 long)
    print(f"    Searching for boolean arrays...")
    bool_arrays = []
    i = 0
    while i < sz - 16:
        if data[i] in (0, 1):
            j = i
            while j < sz and data[j] in (0, 1):
                j += 1
            run_len = j - i
            if run_len >= 32:
                ones = sum(1 for b in data[i:j] if b == 1)
                bool_arrays.append({
                    'addr': hex(start + i),
                    'offset': i,
                    'length': run_len,
                    'ones_count': ones,
                    'zeros_count': run_len - ones,
                    'density': round(ones / run_len, 3),
                    'preview': list(data[i:i+min(64, run_len)]),
                })
            i = j
        else:
            i += 1

    # Filter: keep only interesting ones (not all-zero, some variety)
    bool_arrays = [a for a in bool_arrays if 0.01 < a['density'] < 0.99]
    bool_arrays.sort(key=lambda a: -a['length'])
    print(f"    Found {len(bool_arrays)} boolean arrays (filtered, len>=32, mixed 0/1)")
    for a in bool_arrays[:10]:
        print(f"      {a['addr']}: len={a['length']}, ones={a['ones_count']}, "
              f"density={a['density']}, preview={a['preview'][:24]}...")
    findings.append(('bool_arrays', bool_arrays[:50]))

    # 2. Uint32 ID arrays: sequences of incrementing or clustered uint32s
    print(f"    Searching for uint32 ID arrays...")
    id_arrays = []
    for i in range(0, sz - 64, 4):
        vals = struct.unpack_from('<16I', data, i)
        # Check if they look like IDs: all non-zero, within a reasonable range,
        # and somewhat sequential or clustered
        if all(0 < v < 0x00FFFFFF for v in vals):
            sorted_vals = sorted(vals)
            # Check for sequential or close-together values
            diffs = [sorted_vals[j+1] - sorted_vals[j] for j in range(len(sorted_vals)-1)]
            avg_diff = sum(diffs) / len(diffs) if diffs else 999999
            if avg_diff < 1000:  # Clustered IDs
                id_arrays.append({
                    'addr': hex(start + i),
                    'offset': i,
                    'values': list(vals),
                    'avg_diff': round(avg_diff, 1),
                    'min_val': min(vals),
                    'max_val': max(vals),
                })
                i += 64  # Skip ahead to avoid overlapping matches

    id_arrays.sort(key=lambda a: a['avg_diff'])
    print(f"    Found {len(id_arrays)} candidate uint32 ID arrays")
    for a in id_arrays[:10]:
        print(f"      {a['addr']}: range=[{a['min_val']}-{a['max_val']}], "
              f"avg_diff={a['avg_diff']}, vals={a['values'][:8]}...")
    findings.append(('uint32_id_arrays', id_arrays[:50]))

    # 3. Counter values: scan for small uint32s (1-10000) that sit near known strings
    # Look within 256 bytes of where we find interesting strings
    print(f"    Searching for counter values near interesting strings...")
    counter_strings = [b'discovered', b'unlocked', b'explored', b'completion',
                       b'count', b'total', b'progress', b'collect', b'quest',
                       b'achieve', b'found']
    counters = []
    for cs in counter_strings:
        pos = 0
        while True:
            pos = data.find(cs, pos)
            if pos == -1:
                break
            # Search 256 bytes around for uint32 counters
            scan_start = max(0, pos - 128)
            scan_end = min(sz - 4, pos + len(cs) + 128)
            local_counters = []
            for j in range(scan_start, scan_end, 4):
                val = struct.unpack_from('<I', data, j)[0]
                if 1 <= val <= 10000:
                    local_counters.append({
                        'offset': j,
                        'addr': hex(start + j),
                        'value': val,
                        'distance_from_string': j - pos,
                    })
            if local_counters:
                counters.append({
                    'string': cs.decode('utf-8', errors='replace'),
                    'string_addr': hex(start + pos),
                    'nearby_counters': local_counters[:20],
                })
            pos += 1

    print(f"    Found {len(counters)} string+counter associations")
    for c in counters[:15]:
        print(f"      '{c['string']}' at {c['string_addr']}: "
              f"{len(c['nearby_counters'])} nearby counters, "
              f"values={[nc['value'] for nc in c['nearby_counters'][:8]]}")
    findings.append(('counters_near_strings', counters[:100]))

    # 4. Bitfield search: bytes where multiple bits are set (tracking flags)
    # Look for arrays of bytes 0x00-0xFF where the pattern suggests bitfields
    print(f"    Searching for bitfield arrays...")
    bitfield_candidates = []
    for i in range(0, sz - 32, 1):
        chunk = data[i:i+32]
        # Bitfield heuristic: not all same value, most bytes have 1-4 bits set
        unique = len(set(chunk))
        if unique < 3:
            continue
        bits_set = [bin(b).count('1') for b in chunk]
        avg_bits = sum(bits_set) / len(bits_set)
        if 1.0 <= avg_bits <= 4.0 and all(b < 0x80 for b in chunk):
            # Check it's not just ASCII text
            if not all(32 <= b < 127 for b in chunk):
                bitfield_candidates.append({
                    'addr': hex(start + i),
                    'offset': i,
                    'avg_bits_set': round(avg_bits, 2),
                    'preview_hex': chunk.hex(),
                    'preview_bin': [f'{b:08b}' for b in chunk[:8]],
                })
                # Don't skip too far, but avoid massive overlapping
                # Just collect first N and move on
                if len(bitfield_candidates) >= 200:
                    break

    print(f"    Found {len(bitfield_candidates)} bitfield candidates")
    for bf in bitfield_candidates[:5]:
        print(f"      {bf['addr']}: avg_bits={bf['avg_bits_set']}, "
              f"bin={bf['preview_bin']}")
    findings.append(('bitfields', bitfield_candidates[:50]))

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("  Crimson Desert Differential Memory Scanner")
    print("=" * 72)

    pid = get_pid()
    if not pid:
        print("[ERROR] CrimsonDesert process not found. Is the game running?")
        sys.exit(1)
    print(f"[OK] Found CrimsonDesert at PID {pid}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---- SNAPSHOT 1 ----
    print("\n" + "=" * 72)
    print("  SNAPSHOT 1: Taking initial memory snapshot...")
    print("=" * 72)
    snap1 = take_snapshot(pid, "snap1")

    # Save snapshot 1 hashes for quick comparison
    snap1_hashes = {}
    for name, (start, data) in snap1.items():
        h = hashlib.sha256(data).hexdigest()[:16]
        snap1_hashes[name] = h
        print(f"  snap1['{name}']: {len(data)} bytes, sha256={h}")

    # Save snapshot 1 raw data
    snap1_dir = OUTPUT_DIR / f"snap1_{timestamp}"
    snap1_dir.mkdir(exist_ok=True)
    for name, (start, data) in snap1.items():
        fpath = snap1_dir / f"{name}_{hex(start)}.bin"
        with open(fpath, 'wb') as f:
            f.write(data)
        print(f"  Saved {fpath.name} ({len(data) // 1024}KB)")

    # ---- Deep analysis of snapshot 1 ----
    print("\n" + "=" * 72)
    print("  DEEP ANALYSIS: Examining discovered/completion regions...")
    print("=" * 72)
    deep_results_1 = {}
    for name in DEEP_ANCHORS:
        if name in snap1:
            start, data = snap1[name]
            deep_results_1[name] = deep_analyze_region(name, start, data)

    # Save deep analysis
    deep_file = OUTPUT_DIR / f"deep_analysis_snap1_{timestamp}.json"
    # Convert for JSON serialization
    deep_json = {}
    for name, findings in deep_results_1.items():
        deep_json[name] = {}
        for ftype, fdata in findings:
            deep_json[name][ftype] = fdata
    with open(deep_file, 'w') as f:
        json.dump(deep_json, f, indent=2, default=str)
    print(f"\n  Deep analysis saved to {deep_file.name}")

    # ---- WAIT FOR USER ACTION ----
    # Check for --wait N command-line arg (non-interactive mode)
    wait_seconds = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--wait' and i < len(sys.argv) - 1:
            wait_seconds = int(sys.argv[i + 1])
            break
        elif arg.startswith('--wait='):
            wait_seconds = int(arg.split('=', 1)[1])
            break

    if wait_seconds is not None:
        print(f"\n" + "=" * 72)
        print(f"  NON-INTERACTIVE MODE: waiting {wait_seconds} seconds...")
        print(f"  Go collect an item / discover a location / complete a quest NOW!")
        print("=" * 72)
        for elapsed in range(wait_seconds):
            time.sleep(1)
            remaining = wait_seconds - elapsed - 1
            if remaining % 10 == 0 and remaining > 0:
                print(f"  ... {remaining}s remaining")
        print(f"  Wait complete. Taking snapshot 2...")
    else:
        print("\n" + "=" * 72)
        print("  ACTION REQUIRED")
        print("  Go to the game and collect an item, discover a location,")
        print("  or complete a quest objective.")
        print("")
        print("  Press any key here when done (or wait up to 5 minutes)...")
        print("=" * 72)

        import msvcrt
        waited = 0
        while waited < 300:  # 5 minute max timeout
            if msvcrt.kbhit():
                msvcrt.getch()
                break
            time.sleep(0.5)
            waited += 0.5
            if waited % 30 == 0:
                print(f"  ... waiting ({int(waited)}s elapsed, press any key to continue)...")

    # Verify game is still running
    pid2 = get_pid()
    if not pid2:
        print("[ERROR] Game process gone. Cannot take snapshot 2.")
        sys.exit(1)
    if pid2 != pid:
        print(f"[WARN] PID changed: {pid} -> {pid2}. Game may have restarted.")
        pid = pid2

    # ---- SNAPSHOT 2 ----
    print("\n" + "=" * 72)
    print("  SNAPSHOT 2: Taking post-action memory snapshot...")
    print("=" * 72)
    snap2 = take_snapshot(pid, "snap2")

    # Save snapshot 2 hashes
    snap2_hashes = {}
    for name, (start, data) in snap2.items():
        h = hashlib.sha256(data).hexdigest()[:16]
        snap2_hashes[name] = h
        same = "SAME" if snap1_hashes.get(name) == h else "CHANGED"
        print(f"  snap2['{name}']: {len(data)} bytes, sha256={h}  [{same}]")

    # Save snapshot 2 raw data
    snap2_dir = OUTPUT_DIR / f"snap2_{timestamp}"
    snap2_dir.mkdir(exist_ok=True)
    for name, (start, data) in snap2.items():
        fpath = snap2_dir / f"{name}_{hex(start)}.bin"
        with open(fpath, 'wb') as f:
            f.write(data)

    # ---- DIFF ----
    print("\n" + "=" * 72)
    print("  DIFFING snapshots...")
    print("=" * 72)
    changes = diff_snapshots(snap1, snap2)

    # Analyze
    report = analyze_changes(changes, snap1, snap2)

    # ---- REPORT ----
    print("\n" + "=" * 72)
    print("  DIFF REPORT")
    print("=" * 72)

    total_changes = 0
    for name, region_report in report.items():
        total_changes += region_report['total_changes']
        print(f"\n  Region '{name}': {region_report['total_changes']} bytes changed "
              f"in {region_report.get('num_clusters', 0)} clusters")

        for cluster in region_report.get('details', [])[:25]:  # Show first 25 clusters
            print(f"\n    Cluster at {cluster['cluster_addr']} "
                  f"({cluster['num_bytes_changed']} bytes, span={cluster['cluster_size']})")

            if cluster.get('nearby_strings'):
                print(f"      Nearby strings: {cluster['nearby_strings'][:5]}")

            # Show wide value interpretations
            for key in ['uint32_old', 'int32_old', 'float32_old', 'uint64_old', 'double_old']:
                base = key.replace('_old', '')
                if key in cluster:
                    print(f"      {base}: {cluster[key]} -> {cluster[base + '_new']}")

            # Show individual byte changes (limit to first 10 per cluster)
            for ch in cluster['changes'][:10]:
                print(f"      {ch['addr']}: {ch['old_hex']} -> {ch['new_hex']}  [{ch['type']}]")
            if len(cluster['changes']) > 10:
                print(f"      ... and {len(cluster['changes']) - 10} more byte changes")

    if total_changes == 0:
        print("\n  NO CHANGES DETECTED in any monitored region.")
        print("  This could mean:")
        print("  - The game stores progress in a different memory region")
        print("  - The anchor addresses have shifted (ASLR)")
        print("  - Nothing actually changed in game state")

    # ---- Deep analysis of snapshot 2 and diff ----
    print("\n" + "=" * 72)
    print("  DEEP ANALYSIS: Post-action region examination...")
    print("=" * 72)
    deep_results_2 = {}
    for name in DEEP_ANCHORS:
        if name in snap2:
            start, data = snap2[name]
            deep_results_2[name] = deep_analyze_region(name, start, data)

    # Compare deep analysis results
    print("\n" + "=" * 72)
    print("  DEEP ANALYSIS DIFF")
    print("=" * 72)
    for name in DEEP_ANCHORS:
        if name in deep_results_1 and name in deep_results_2:
            # Compare boolean arrays
            ba1 = {f['addr']: f for ftype, fdata in deep_results_1[name]
                   for f in fdata if ftype == 'bool_arrays'}
            ba2 = {f['addr']: f for ftype, fdata in deep_results_2[name]
                   for f in fdata if ftype == 'bool_arrays'}
            # Find arrays that changed
            for addr in ba1:
                if addr in ba2:
                    if ba1[addr]['ones_count'] != ba2[addr]['ones_count']:
                        delta = ba2[addr]['ones_count'] - ba1[addr]['ones_count']
                        print(f"  [{name}] Bool array at {addr}: "
                              f"ones changed {ba1[addr]['ones_count']} -> {ba2[addr]['ones_count']} "
                              f"(delta={delta:+d})")

    # ---- Save full report ----
    report_file = OUTPUT_DIR / f"diff_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'pid': pid,
            'anchors': {k: hex(v) for k, v in ANCHORS.items()},
            'snap1_hashes': snap1_hashes,
            'snap2_hashes': snap2_hashes,
            'regions': report,
        }, f, indent=2, default=str)
    print(f"\n  Full report saved to {report_file}")

    # Summary
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Total bytes changed across all regions: {total_changes}")
    for name, region_report in report.items():
        n = region_report['total_changes']
        if n > 0:
            types = defaultdict(int)
            for cluster in region_report.get('details', []):
                for ch in cluster['changes']:
                    types[ch['type']] += 1
            type_str = ", ".join(f"{t}={c}" for t, c in sorted(types.items(), key=lambda x: -x[1]))
            print(f"    {name}: {n} changes ({type_str})")
        else:
            print(f"    {name}: no changes")

    print(f"\n  Output directory: {OUTPUT_DIR}")
    print(f"  Snapshot files: snap1_{timestamp}/ and snap2_{timestamp}/")
    print(f"  Deep analysis: deep_analysis_snap1_{timestamp}.json")
    print(f"  Diff report: diff_report_{timestamp}.json")
    print("=" * 72)


if __name__ == '__main__':
    main()
