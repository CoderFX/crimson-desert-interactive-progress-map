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
SCAN_RADIUS = 800  # game units
ITEM_OFFSET_RANGE = (800, 1000)  # byte range from position where item keys live
SCAN_INTERVAL = 3  # seconds between scans

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

    def scan_gold_npcs(self):
        """Scan memory for nearby NPCs carrying gold bars."""
        player = self.get_player_pos()
        if not player:
            return []

        px, py, pz = player
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

            if (mbi.State == 0x1000 and mbi.Protect == 0x04 and
                    4096 < mbi.RegionSize < 16 * 1024 * 1024):
                sz = min(mbi.RegionSize, 16 * 1024 * 1024)
                buf = ctypes.create_string_buffer(sz)
                br = ctypes.c_size_t()
                if k32.ReadProcessMemory(self.handle, ctypes.c_uint64(mbi.BaseAddress),
                                          buf, sz, ctypes.byref(br)):
                    data = buf.raw[:br.value]
                    mb_scanned += br.value / 1048576

                    # Scan for position floats near player
                    needle = struct.pack('<f', round(px))[:2]
                    pos = 0
                    while True:
                        pos = data.find(needle, pos)
                        if pos == -1 or pos + ITEM_OFFSET_RANGE[1] > len(data):
                            break

                        fx = struct.unpack_from('<f', data, pos)[0]
                        if abs(fx - px) < SCAN_RADIUS:
                            fz_off = pos + 8
                            if fz_off + 4 <= len(data):
                                fz = struct.unpack_from('<f', data, fz_off)[0]
                                if abs(fz - pz) < SCAN_RADIUS:
                                    fy = struct.unpack_from('<f', data, pos + 4)[0]
                                    if (abs(fy) < 5000 and
                                            not (abs(fx - px) < 1 and abs(fz - pz) < 1)):
                                        # Check for gold bar in item range
                                        for g in range(ITEM_OFFSET_RANGE[0],
                                                       ITEM_OFFSET_RANGE[1], 4):
                                            if pos + g + 4 <= len(data):
                                                val = struct.unpack_from('<I', data, pos + g)[0]
                                                if val == GOLD_BAR_KEY:
                                                    dist = ((fx - px) ** 2 + (fz - pz) ** 2) ** 0.5
                                                    lat, lng = game_to_map(fx, fz)
                                                    gold_npcs.append({
                                                        'x': round(fx, 1),
                                                        'y': round(fy, 1),
                                                        'z': round(fz, 1),
                                                        'lat': round(lat, 8),
                                                        'lng': round(lng, 8),
                                                        'dist': round(dist, 0),
                                                    })
                                                    break
                        pos += 2

            addr = mbi.BaseAddress + mbi.RegionSize
            if addr <= mbi.BaseAddress:
                break

        # Deduplicate
        seen = set()
        unique = []
        for n in gold_npcs:
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
