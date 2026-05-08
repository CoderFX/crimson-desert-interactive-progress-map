"""
Gold Bar NPC Scanner for Crimson Desert
Finds NPCs carrying gold bars by searching for item key 53 in dense
item clusters, then looking for position floats 300-600 bytes before.

Usage: Run as Administrator
  python tools/gold_scanner.py
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
WS_PORT = 7892
GOLD_BAR_KEY = 53
SCAN_RADIUS = 300
SCAN_INTERVAL = 5  # seconds - full memory scan takes ~60s
MIN_ITEMS_CLUSTER = 12  # minimum item-like values near gold key

# Position floats are 300-600 bytes BEFORE the gold key
POS_SEARCH_MIN = 200
POS_SEARCH_MAX = 650

# Static position addresses (set by CD Companion hooks)
STATIC_X = 0x145efe9c0
STATIC_Y = 0x145efe9c4
STATIC_Z = 0x145efe9c8

CAL = [
    {"game": [-12127.14, 7.69], "map": [-0.9052, 0.7787]},
    {"game": [-3690.79, -6117.51], "map": [-0.5556, 0.5249]},
]

def game_to_map(gx, gz):
    g1, g2 = CAL[0]["game"], CAL[1]["game"]
    m1, m2 = CAL[0]["map"], CAL[1]["map"]
    lng = m1[0] + (gx - g1[0]) * (m2[0] - m1[0]) / (g2[0] - g1[0])
    lat = m1[1] + (gz - g1[1]) * (m2[1] - m1[1]) / (g2[1] - g1[1])
    return lat, lng


class GoldScanner:
    def __init__(self):
        self.pm = None
        self.handle = None

    def attach(self):
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            self.handle = ctypes.windll.kernel32.OpenProcess(
                0x0010 | 0x0400, False, self.pm.process_id)
            log.info(f"Attached to {PROCESS_NAME} (PID {self.pm.process_id})")
            return True
        except Exception as e:
            log.error(f"Failed to attach: {e}")
            return False

    def get_player_pos(self):
        try:
            x = self.pm.read_float(STATIC_X)
            y = self.pm.read_float(STATIC_Y)
            z = self.pm.read_float(STATIC_Z)
            return (x, y, z)
        except:
            return None

    def scan_gold_npcs(self):
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

        GOLD = struct.pack('<I', GOLD_BAR_KEY)
        mbi = MBI64()
        addr = 0
        results = []
        mb = 0

        while mb < 8000:
            if not k32.VirtualQueryEx(self.handle, ctypes.c_uint64(addr),
                                       ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if (mbi.State == 0x1000 and (mbi.Protect & 0xFF) in (0x04, 0x40)
                    and mbi.RegionSize >= 4096):
                sz = min(mbi.RegionSize, 32 * 1024 * 1024)
                buf = ctypes.create_string_buffer(sz)
                br = ctypes.c_size_t()
                if k32.ReadProcessMemory(self.handle, ctypes.c_uint64(mbi.BaseAddress),
                                          buf, sz, ctypes.byref(br)):
                    data = buf.raw[:br.value]
                    mb += br.value / 1048576

                    # Search for gold bar key (u32 = 53)
                    pos = 0
                    while True:
                        pos = data.find(GOLD, pos)
                        if pos == -1:
                            break
                        if pos % 4 != 0:
                            pos += 1
                            continue

                        # Count item-like values (1-500) in ±100 bytes
                        items = 0
                        for j in range(max(0, pos - 100), min(len(data) - 4, pos + 100), 4):
                            v = struct.unpack_from('<I', data, j)[0]
                            if 1 <= v <= 500:
                                items += 1

                        if items >= MIN_ITEMS_CLUSTER:
                            # Look for position floats 200-650 bytes BEFORE the gold key
                            for p in range(max(0, pos - POS_SEARCH_MAX),
                                           max(0, pos - POS_SEARCH_MIN), 4):
                                if p + 12 > len(data):
                                    break
                                fx = struct.unpack_from('<f', data, p)[0]
                                if abs(fx - px) < SCAN_RADIUS:
                                    fy = struct.unpack_from('<f', data, p + 4)[0]
                                    fz = struct.unpack_from('<f', data, p + 8)[0]
                                    if (abs(fz - pz) < SCAN_RADIUS
                                            and abs(fy) < 10000
                                            and not (abs(fx - px) < 1 and abs(fz - pz) < 1)):
                                        dist = ((fx - px) ** 2 + (fz - pz) ** 2) ** 0.5
                                        lat, lng = game_to_map(fx, fz)
                                        results.append({
                                            'x': round(fx, 1),
                                            'y': round(fy, 1),
                                            'z': round(fz, 1),
                                            'lat': round(lat, 8),
                                            'lng': round(lng, 8),
                                            'dist': round(dist, 0),
                                        })
                                        break
                        pos += 4

            addr = mbi.BaseAddress + mbi.RegionSize
            if addr <= mbi.BaseAddress:
                break

        # Deduplicate
        seen = set()
        unique = []
        for n in sorted(results, key=lambda x: x['dist']):
            k = (round(n['x'] / 10) * 10, round(n['z'] / 10) * 10)
            if k not in seen:
                seen.add(k)
                unique.append(n)

        return unique


# WebSocket
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
    global clients
    prev_count = -1
    while True:
        try:
            npcs = scanner.scan_gold_npcs()

            if len(npcs) != prev_count:
                prev_count = len(npcs)
                log.info(f"Gold bar carriers: {len(npcs)}")
                for n in npcs[:10]:
                    log.info(f"  ({n['x']:.0f}, {n['z']:.0f}) dist={n['dist']:.0f}")

            msg = json.dumps({
                "type": "gold_npcs",
                "npcs": npcs,
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
        log.error("Could not attach. Run as Administrator.")
        sys.exit(1)

    player = scanner.get_player_pos()
    if player:
        log.info(f"Player at ({player[0]:.0f}, {player[1]:.0f}, {player[2]:.0f})")

    log.info("Initial scan...")
    npcs = scanner.scan_gold_npcs()
    log.info(f"Found {len(npcs)} gold bar carrier(s)")

    log.info(f"WebSocket on ws://localhost:{WS_PORT}")
    log.info(f"Scanning every {SCAN_INTERVAL}s, radius {SCAN_RADIUS}u")

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await scan_loop(scanner)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down")
