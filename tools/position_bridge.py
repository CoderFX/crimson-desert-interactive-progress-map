"""
Minimal Position Bridge for Crimson Desert
Reads player position from game memory and broadcasts via WebSocket.
Compatible with CD Companion's protocol so our map auto-connects.

Usage: Run as Administrator
  python tools/position_bridge.py

Requires: pip install pymem websockets
"""

import asyncio
import json
import logging
import math
import struct
import sys
import time

import pymem
import pymem.process
import websockets
import websockets.server

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger('position_bridge')

PROCESS_NAME = "CrimsonDesert.exe"
WS_PORT = 7891

# AOB patterns from CD Companion (proven to work)
AOB_POS = b'\x0F\x11\x99\x90\x00\x00\x00'  # movups [rcx+0x90], xmm3

# Coordinate transform constants (game coords -> map lat/lng)
# Calibrated from CD Companion's coord_math.py
# Game X range: ~-12000 to +12000, Game Z range: ~-12000 to +12000
# Map lng: ~-1.38 to -0.48, Map lat: ~0.38 to 0.95

class PositionReader:
    def __init__(self):
        self.pm = None
        self.base = None
        self.static_x_addr = None
        self.static_y_addr = None
        self.static_z_addr = None

    def attach(self):
        """Attach to the game process."""
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            self.base = self.pm.process_base.lpBaseOfDll
            log.info(f"Attached to {PROCESS_NAME} (PID {self.pm.process_id}, base {hex(self.base)})")
            self._find_position_addresses()
            return True
        except Exception as e:
            log.error(f"Failed to attach: {e}")
            return False

    def _find_position_addresses(self):
        """Find static position addresses by scanning for known patterns."""
        # Method: scan for the vmovsd instruction pattern that writes to static global XYZ
        # Pattern: C5 FB 11 05 [disp32] (vmovsd [rip+disp], xmm0)
        pattern = b'\xC5\xFB\x11\x05'

        module = pymem.process.module_from_name(self.pm.process_handle, PROCESS_NAME)
        if not module:
            log.warning("Could not find main module, trying direct scan")
            return

        log.info(f"Scanning {PROCESS_NAME} for position addresses...")

        try:
            # Scan the main module for the pattern
            data = self.pm.read_bytes(module.lpBaseOfDll, min(module.SizeOfImage, 100_000_000))
        except Exception as e:
            log.warning(f"Could not read module: {e}")
            return

        hits = []
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1:
                break
            # Read the RIP-relative displacement
            disp = struct.unpack_from('<i', data, pos + 4)[0]
            # Calculate absolute address: rip (instruction end) + displacement
            abs_addr = module.lpBaseOfDll + pos + 8 + disp
            hits.append((pos, abs_addr))
            pos += 1

        log.info(f"Found {len(hits)} vmovsd candidates")

        # Try to find three consecutive static addresses (X, Y, Z)
        # They should be close to each other in memory
        for i, (off, addr) in enumerate(hits):
            try:
                val = struct.unpack('<f', self.pm.read_bytes(addr, 4))[0]
                if -20000 < val < 20000 and val != 0:
                    # Check if next address is nearby and also a valid coordinate
                    for j, (off2, addr2) in enumerate(hits[i+1:i+20], i+1):
                        val2 = struct.unpack('<f', self.pm.read_bytes(addr2, 4))[0]
                        if abs(addr2 - addr) < 32 and -20000 < val2 < 20000:
                            # Found a pair, look for third
                            for k, (off3, addr3) in enumerate(hits[j+1:j+20], j+1):
                                val3 = struct.unpack('<f', self.pm.read_bytes(addr3, 4))[0]
                                if abs(addr3 - addr) < 32 and -20000 < val3 < 20000:
                                    self.static_x_addr = addr
                                    self.static_y_addr = addr2
                                    self.static_z_addr = addr3
                                    log.info(f"Position addresses found: X={hex(addr)} ({val:.1f}), Y={hex(addr2)} ({val2:.1f}), Z={hex(addr3)} ({val3:.1f})")
                                    return
            except Exception:
                continue

        log.warning("Could not find static position addresses via vmovsd scan")
        log.info("Falling back to entity hook method...")

    def read_position(self):
        """Read current player position. Returns (x, y, z) or None."""
        if not self.pm:
            return None

        try:
            if self.static_x_addr:
                x = struct.unpack('<f', self.pm.read_bytes(self.static_x_addr, 4))[0]
                y = struct.unpack('<f', self.pm.read_bytes(self.static_y_addr, 4))[0]
                z = struct.unpack('<f', self.pm.read_bytes(self.static_z_addr, 4))[0]
                if x == 0 and y == 0 and z == 0:
                    return None
                return (x, y, z)
        except Exception:
            return None
        return None

    def game_to_map(self, x, y, z):
        """Convert game coordinates to map lat/lng using affine transform."""
        # Calibration from CD Companion's coord_math.py
        # These are approximate - may need fine-tuning
        # Game coords: X is east-west, Z is north-south, Y is altitude
        # Map coords: lng is east-west, lat is north-south

        # Linear transform based on known reference points:
        # Hernand Castle: game ~(-8400, ?, 3200) -> map (0.621, -0.840)
        # Using the transform from CD Companion source
        lng = x * 5.381e-05 + (-0.3217)
        lat = z * (-5.381e-05) + (0.8678)
        return lat, lng


# WebSocket server
clients = set()

async def ws_handler(websocket):
    clients.add(websocket)
    log.info(f"Client connected ({len(clients)} total)")
    try:
        async for msg in websocket:
            pass  # We only broadcast, don't receive
    finally:
        clients.discard(websocket)
        log.info(f"Client disconnected ({len(clients)} total)")


async def broadcast_position(reader):
    """Periodically read position and broadcast to all clients."""
    last_pos = None
    while True:
        pos = reader.read_position()
        if pos and pos != last_pos:
            x, y, z = pos
            lat, lng = reader.game_to_map(x, y, z)
            msg = json.dumps({
                "type": "position",
                "lng": round(lng, 8),
                "lat": round(lat, 8),
                "x": round(x, 1),
                "y": round(y, 1),
                "z": round(z, 1),
                "realm": "pywel"
            })
            dead = set()
            for ws in clients:
                try:
                    await ws.send(msg)
                except Exception:
                    dead.add(ws)
            clients -= dead
            last_pos = pos
        await asyncio.sleep(0.5)  # 2Hz update rate


async def main():
    reader = PositionReader()

    if not reader.attach():
        log.error("Could not attach to game. Is it running? Try running as Administrator.")
        sys.exit(1)

    pos = reader.read_position()
    if pos:
        x, y, z = pos
        lat, lng = reader.game_to_map(x, y, z)
        log.info(f"Initial position: game({x:.0f}, {y:.0f}, {z:.0f}) -> map({lat:.5f}, {lng:.5f})")
    else:
        log.warning("Could not read initial position - will keep trying")

    log.info(f"Starting WebSocket server on ws://localhost:{WS_PORT}")

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        log.info("Position bridge running. Open the map and connect.")
        log.info("Press Ctrl+C to stop.")
        await broadcast_position(reader)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down")
