"""
Gold Bar NPC Scanner for Crimson Desert
Scans game memory for nearby NPCs carrying gold bars and broadcasts
their positions to the interactive map via WebSocket.

Run alongside the position bridge / CD Companion.

Usage: Run as Administrator
  python tools/gold_scanner.py

Requires: pip install pymem websockets
"""

import asyncio
import ctypes
import ctypes.wintypes as wt
import json
import logging
import struct
import sys
import time

import pymem
import websockets.server

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger('gold_scanner')

PROCESS_NAME = "CrimsonDesert.exe"
WS_PORT = 7892  # Separate port from CD Companion (7891)

# Known addresses (from CD Companion's hook)
STATIC_X = 0x145efe9c0
STATIC_Y = 0x145efe9c4
STATIC_Z = 0x145efe9c8

GOLD_BAR_KEY = 53
SCAN_RADIUS = 500  # game units
SCAN_INTERVAL = 2  # seconds between scans
GOLD_SEARCH_WINDOW = 8192  # bytes before/after a gold key to search for NPC coordinates
READ_CHUNK_SIZE = 8 * 1024 * 1024
READ_OVERLAP = GOLD_SEARCH_WINDOW + 128
VALID_ITEM_KEY_MAX = 1000

MEM_COMMIT = 0x1000
PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_GUARD = 0x100
READABLE_PROTECTS = {
    PAGE_READONLY,
    PAGE_READWRITE,
    PAGE_WRITECOPY,
    PAGE_EXECUTE_READ,
    PAGE_EXECUTE_READWRITE,
    PAGE_EXECUTE_WRITECOPY,
}

# Coordinate transform (game -> map lat/lng)
# From CD Companion's calibration data
CAL_POINTS = [
    {"game": [-12127.14, 7.69], "map": [-0.9052, 0.7787]},
    {"game": [-3690.79, -6117.51], "map": [-0.5556, 0.5249]},
]

def game_to_map(gx, gz):
    """Convert game X,Z to map lng,lat using linear interpolation."""
    g1, g2 = CAL_POINTS[0]["game"], CAL_POINTS[1]["game"]
    m1, m2 = CAL_POINTS[0]["map"], CAL_POINTS[1]["map"]
    # Linear interpolation
    dx = g2[0] - g1[0]
    dz = g2[1] - g1[1]
    lng = m1[0] + (gx - g1[0]) * (m2[0] - m1[0]) / dx
    lat = m1[1] + (gz - g1[1]) * (m2[1] - m1[1]) / dz
    return lat, lng


class GoldScanner:
    def __init__(self):
        self.pm = None
        self.handle = None

    def attach(self):
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            k32 = ctypes.windll.kernel32
            self.handle = k32.OpenProcess(0x0010 | 0x0400, False, self.pm.process_id)
            log.info(f"Attached to {PROCESS_NAME} (PID {self.pm.process_id})")
            return True
        except Exception as e:
            log.error(f"Failed to attach: {e}")
            return False

    def get_player_pos(self):
        try:
            x = struct.unpack('<f', self.pm.read_bytes(STATIC_X, 4))[0]
            y = struct.unpack('<f', self.pm.read_bytes(STATIC_Y, 4))[0]
            z = struct.unpack('<f', self.pm.read_bytes(STATIC_Z, 4))[0]
            return (x, y, z)
        except:
            return None

    @staticmethod
    def is_readable_region(mbi):
        if mbi.State != MEM_COMMIT:
            return False
        if mbi.Protect & PAGE_GUARD:
            return False
        return (mbi.Protect & 0xff) in READABLE_PROTECTS

    @staticmethod
    def is_candidate_position(x, y, z, px, py, pz):
        if x is None or y is None or z is None:
            return False
        if not all(-100000.0 < v < 100000.0 for v in (x, y, z)):
            return False
        if abs(x - px) > SCAN_RADIUS or abs(z - pz) > SCAN_RADIUS:
            return False
        if abs(y - py) > 1500 and abs(y) > 5000:
            return False
        if abs(x - px) < 1 and abs(y - py) < 5 and abs(z - pz) < 1:
            return False
        return True

    @staticmethod
    def plausible_item_cluster(data, pos, width):
        """Keep u16/u32 key detection broad without accepting every incidental 53."""
        start = max(0, pos - 256)
        end = min(len(data) - width, pos + 256)
        fmt = '<I' if width == 4 else '<H'
        count = 0
        for off in range(start + ((pos - start) % width), end + 1, width):
            try:
                val = struct.unpack_from(fmt, data, off)[0]
            except struct.error:
                continue
            if 1 <= val <= VALID_ITEM_KEY_MAX:
                count += 1
                if count >= (2 if width == 4 else 3):
                    return True
        return width == 4 and count >= 1

    def positions_near_gold(self, data, gold_pos, player, base_addr, key_width):
        px, py, pz = player
        found = []
        start = max(0, gold_pos - GOLD_SEARCH_WINDOW)
        end = min(len(data), gold_pos + GOLD_SEARCH_WINDOW)

        pos = start + ((4 - (start % 4)) % 4)
        while pos + 12 <= end:
            try:
                fx, fy, fz = struct.unpack_from('<fff', data, pos)
            except struct.error:
                break
            if self.is_candidate_position(fx, fy, fz, px, py, pz):
                found.append((fx, fy, fz, pos, 'f32'))
            pos += 4

        pos = start + ((4 - (start % 4)) % 4)
        while pos + 24 <= end:
            try:
                fx, fy, fz = struct.unpack_from('<ddd', data, pos)
            except struct.error:
                break
            if self.is_candidate_position(fx, fy, fz, px, py, pz):
                found.append((fx, fy, fz, pos, 'f64'))
            pos += 4

        matches = []
        for fx, fy, fz, pos, coord_fmt in found:
            dist = ((fx - px) ** 2 + (fz - pz) ** 2) ** 0.5
            lat, lng = game_to_map(fx, fz)
            matches.append({
                'x': round(fx, 1),
                'y': round(fy, 1),
                'z': round(fz, 1),
                'lat': round(lat, 8),
                'lng': round(lng, 8),
                'dist': round(dist, 0),
                'addr': hex(base_addr + pos),
                'gold_offset': gold_pos - pos,
                'coord_fmt': coord_fmt,
                'key_fmt': f'u{key_width * 8}',
            })
        return matches

    def scan_buffer_for_gold_npcs(self, data, base_addr, player):
        matches = []
        for pattern, width in (
            (struct.pack('<I', GOLD_BAR_KEY), 4),
            (struct.pack('<H', GOLD_BAR_KEY), 2),
        ):
            pos = 0
            while True:
                pos = data.find(pattern, pos)
                if pos == -1:
                    break
                if self.plausible_item_cluster(data, pos, width):
                    matches.extend(self.positions_near_gold(data, pos, player, base_addr, width))
                pos += width
        return matches

    def scan_gold_npcs(self):
        """Scan memory for nearby NPCs carrying gold bars."""
        player = self.get_player_pos()
        if not player:
            return []

        k32 = ctypes.windll.kernel32

        class MBI64(ctypes.Structure):
            _fields_ = [
                ('BaseAddress', ctypes.c_uint64), ('AllocationBase', ctypes.c_uint64),
                ('AllocationProtect', wt.DWORD), ('__a1', wt.DWORD),
                ('RegionSize', ctypes.c_uint64), ('State', wt.DWORD),
                ('Protect', wt.DWORD), ('Type', wt.DWORD), ('__a2', wt.DWORD),
            ]

        mbi = MBI64()
        addr = 0
        gold_npcs = []
        mb_scanned = 0

        while mb_scanned < 6000:
            if not k32.VirtualQueryEx(self.handle, ctypes.c_uint64(addr),
                                      ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if self.is_readable_region(mbi) and mbi.RegionSize >= 4096:
                region_left = mbi.RegionSize
                region_off = 0
                while region_left > 0:
                    sz = min(region_left, READ_CHUNK_SIZE + READ_OVERLAP)
                    chunk_addr = mbi.BaseAddress + region_off
                    buf = ctypes.create_string_buffer(sz)
                    br = ctypes.c_size_t()
                    if k32.ReadProcessMemory(self.handle, ctypes.c_uint64(chunk_addr),
                                              buf, sz, ctypes.byref(br)):
                        data = buf.raw[:br.value]
                        mb_scanned += br.value / 1048576
                        gold_npcs.extend(
                            self.scan_buffer_for_gold_npcs(data, chunk_addr, player)
                        )
                    if region_left <= READ_CHUNK_SIZE:
                        break
                    region_off += READ_CHUNK_SIZE
                    region_left -= READ_CHUNK_SIZE

            addr = mbi.BaseAddress + mbi.RegionSize
            if addr <= mbi.BaseAddress:
                break

        # Deduplicate
        seen = set()
        unique = []
        for n in sorted(gold_npcs, key=lambda item: item['dist']):
            k = (round(n['x'] / 10) * 10, round(n['z'] / 10) * 10)
            if k not in seen:
                seen.add(k)
                unique.append(n)

        return unique


# WebSocket server
clients = set()

async def ws_handler(websocket):
    global clients
    clients.add(websocket)
    log.info(f"Map client connected ({len(clients)} total)")
    try:
        async for msg in websocket:
            pass
    finally:
        clients.discard(websocket)


async def scan_loop(scanner):
    """Periodically scan and broadcast gold bar NPC positions."""
    global clients
    prev_count = -1
    while True:
        try:
            npcs = scanner.scan_gold_npcs()
            player = scanner.get_player_pos()

            if len(npcs) != prev_count:
                prev_count = len(npcs)
                if npcs:
                    log.info(f"Found {len(npcs)} gold bar carrier(s)!")
                    for n in npcs:
                        log.info(f"  ({n['x']:.0f}, {n['z']:.0f}) dist={n['dist']:.0f}")

            msg = json.dumps({
                "type": "gold_npcs",
                "npcs": npcs,
                "player": {"x": player[0], "y": player[1], "z": player[2]} if player else None,
                "timestamp": time.time()
            })

            dead = set()
            for ws in clients:
                try:
                    await ws.send(msg)
                except:
                    dead.add(ws)
            clients -= dead

        except Exception as e:
            log.warning(f"Scan error: {e}")

        await asyncio.sleep(SCAN_INTERVAL)


async def main():
    scanner = GoldScanner()
    if not scanner.attach():
        log.error("Could not attach to game. Run as Administrator.")
        sys.exit(1)

    # Quick test
    player = scanner.get_player_pos()
    if player:
        log.info(f"Player at ({player[0]:.0f}, {player[1]:.0f}, {player[2]:.0f})")
    npcs = scanner.scan_gold_npcs()
    log.info(f"Initial scan: {len(npcs)} gold bar carrier(s)")

    log.info(f"Starting gold scanner WebSocket on ws://localhost:{WS_PORT}")
    log.info(f"Scanning every {SCAN_INTERVAL}s within {SCAN_RADIUS} units")

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await scan_loop(scanner)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down")
