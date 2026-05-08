"""
Gold Bar NPC Scanner for Crimson Desert
Scans game memory for nearby NPCs carrying gold bars.
Broadcasts positions to the interactive map via WebSocket.

Approach: Find position float triplets near player, then check
a wide range of offsets for gold bar item key (53).

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
SCAN_INTERVAL = 3

# We check offsets 0 to 2048 from each position match for gold bar key
# The original working find was at offset +884
ITEM_SCAN_RANGE = 2048

# Minimum number of item-like values (1-500) near the gold key to confirm it's an inventory
MIN_NEARBY_ITEMS = 8

# Coordinate transform
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
            # Find static position addresses dynamically
            x = self.pm.read_float(0x145efe9c0)
            y = self.pm.read_float(0x145efe9c4)
            z = self.pm.read_float(0x145efe9c8)
            return (x, y, z)
        except:
            return None

    def scan_gold_npcs(self):
        """Find NPCs near player that have gold bar key in their memory."""
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
        results = []
        mb = 0

        # Pack player X as search needle (match first 3 bytes of the float)
        px_bytes = struct.pack('<f', px)

        while mb < 6000:
            if not k32.VirtualQueryEx(self.handle, ctypes.c_uint64(addr),
                                       ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            # Only scan committed, writable memory (where game objects live)
            if (mbi.State == 0x1000 and mbi.Protect == 0x04 and
                    4096 < mbi.RegionSize < 16 * 1024 * 1024):
                sz = min(mbi.RegionSize, 16 * 1024 * 1024)
                buf = ctypes.create_string_buffer(sz)
                br = ctypes.c_size_t()
                if k32.ReadProcessMemory(self.handle, ctypes.c_uint64(mbi.BaseAddress),
                                          buf, sz, ctypes.byref(br)):
                    data = buf.raw[:br.value]
                    mb += br.value / 1048576

                    # Search for position floats near player
                    pos = 0
                    while True:
                        # Match first 2 bytes of player X float for speed
                        pos = data.find(px_bytes[:2], pos)
                        if pos == -1 or pos + ITEM_SCAN_RANGE > len(data):
                            break

                        # Verify full float triple
                        try:
                            fx = struct.unpack_from('<f', data, pos)[0]
                        except:
                            pos += 2
                            continue

                        if abs(fx - px) > SCAN_RADIUS:
                            pos += 2
                            continue

                        # Check Z (8 bytes after X, with Y in between)
                        if pos + 12 > len(data):
                            pos += 2
                            continue

                        fy = struct.unpack_from('<f', data, pos + 4)[0]
                        fz = struct.unpack_from('<f', data, pos + 8)[0]

                        if abs(fz - pz) > SCAN_RADIUS:
                            pos += 2
                            continue

                        # Skip if it's the player's own position
                        if abs(fx - px) < 1 and abs(fz - pz) < 1:
                            pos += 2
                            continue

                        # Sanity check on Y (height)
                        if abs(fy) > 10000:
                            pos += 2
                            continue

                        # Now check offsets 0 to ITEM_SCAN_RANGE for gold bar key (53)
                        end_check = min(len(data), pos + ITEM_SCAN_RANGE)
                        has_gold = False
                        gold_offset = -1

                        for g in range(pos, end_check - 4, 4):
                            val = struct.unpack_from('<I', data, g)[0]
                            if val == GOLD_BAR_KEY:
                                # Verify this looks like an inventory by counting nearby item keys
                                item_count = 0
                                check_start = max(pos, g - 200)
                                check_end = min(end_check, g + 200)
                                for j in range(check_start, check_end - 4, 4):
                                    v = struct.unpack_from('<I', data, j)[0]
                                    if 1 <= v <= 500:
                                        item_count += 1

                                if item_count >= MIN_NEARBY_ITEMS:
                                    has_gold = True
                                    gold_offset = g - pos
                                    break

                        if has_gold:
                            dist = ((fx - px) ** 2 + (fz - pz) ** 2) ** 0.5
                            lat, lng = game_to_map(fx, fz)
                            results.append({
                                'x': round(fx, 1),
                                'y': round(fy, 1),
                                'z': round(fz, 1),
                                'lat': round(lat, 8),
                                'lng': round(lng, 8),
                                'dist': round(dist, 0),
                                'gold_offset': gold_offset,
                            })

                        pos += 2

            addr = mbi.BaseAddress + mbi.RegionSize
            if addr <= mbi.BaseAddress:
                break

        # Deduplicate by rounding position
        seen = set()
        unique = []
        for n in sorted(results, key=lambda x: x['dist']):
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
                    for n in npcs[:10]:
                        log.info(f"  ({n['x']:.0f}, {n['z']:.0f}) dist={n['dist']:.0f} offset=+{n['gold_offset']}")

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

    player = scanner.get_player_pos()
    if player:
        log.info(f"Player at ({player[0]:.0f}, {player[1]:.0f}, {player[2]:.0f})")

    log.info(f"Initial scan...")
    npcs = scanner.scan_gold_npcs()
    log.info(f"Found {len(npcs)} gold bar carrier(s)")

    log.info(f"WebSocket on ws://localhost:{WS_PORT}")
    log.info(f"Scanning every {SCAN_INTERVAL}s, radius {SCAN_RADIUS}u, min {MIN_NEARBY_ITEMS} items to confirm")

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await scan_loop(scanner)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down")
