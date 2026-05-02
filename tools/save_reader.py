"""
Crimson Desert Save File Reader
Decrypts and parses save files to extract game progress.
Based on the documented SAVE format: ChaCha20 encryption + LZ4 compression + PARC serialization.

Usage:
  python tools/save_reader.py [slot_number]
  python tools/save_reader.py --list-classes
  python tools/save_reader.py --export-progress
"""

import struct
import sys
import os
import json
import hashlib
import hmac as hmac_mod

import lz4.block
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms

# --- Save file crypto ---

SAVE_MAGIC = b'SAVE'

# Base key (31 bytes + null terminator)
_SAVE_BASE_KEY = bytes.fromhex(
    "C41B8E730DF259A637CC04E9B12F9668DA107A853E61F9224DB80AD75C13EF90"
)[:31]

def _generate_save_key(version):
    """Derive the ChaCha20 key by XOR of base key with prefix+secret."""
    if version == 2:
        prefix = b"^Pearl--#Abyss__@!!"
    elif version == 1:
        prefix = b'^Qgbrm/.#@`zsr]\\@rvfal#"'
    else:
        raise ValueError(f"Unsupported save version {version}")

    key_material = prefix + b"PRIVATE_HMAC_SECRET_CHECK"
    key = bytes(x ^ y for x, y in zip(_SAVE_BASE_KEY, key_material)) + b"\x00"
    return key

def decrypt_save(filepath):
    """Decrypt and decompress a save file, return raw PARC bytes."""
    with open(filepath, 'rb') as f:
        data = f.read()

    magic = data[0:4]
    if magic != SAVE_MAGIC:
        raise ValueError(f"Not a save file: {magic}")

    version = struct.unpack_from('<H', data, 4)[0]

    # Header layout (128 bytes):
    # 0x00: SAVE magic (4)
    # 0x04: version (2) + flags (2)
    # 0x08: game data (varies)
    # The exact offsets for sizes/nonce/hmac need to match the actual format
    # Let's read them from the documented positions

    # Try the documented offsets first
    # offset 0x12 (18): uncompressed_size
    # offset 0x16 (22): compressed_size
    # offset 0x1A (26): nonce (16 bytes)
    # offset 0x2A (42): hmac (32 bytes)
    # offset 0x80 (128): encrypted payload

    # But the header also has game-specific fields between 0x08-0x12
    # Let's try to find the right offsets by checking if payload size makes sense

    file_size = len(data)
    header_size = 128
    payload_size = file_size - header_size

    # Read potential size fields and check which makes sense
    for size_offset in [0x12, 0x10, 0x14, 0x16]:
        for comp_offset in [size_offset + 4, size_offset + 2]:
            uncomp = struct.unpack_from('<I', data, size_offset)[0]
            comp = struct.unpack_from('<I', data, comp_offset)[0]
            if comp == payload_size and uncomp > comp:
                nonce_offset = comp_offset + 4
                nonce = data[nonce_offset:nonce_offset + 16]
                hmac_offset = nonce_offset + 16
                stored_hmac = data[hmac_offset:hmac_offset + 32]

                encrypted_payload = data[header_size:header_size + comp]
                key = _generate_save_key(version)

                # Decrypt
                cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
                compressed = cipher.decryptor().update(encrypted_payload)

                # Verify HMAC
                from cryptography.hazmat.primitives.hmac import HMAC as CHMAC
                from cryptography.hazmat.primitives.hashes import SHA256
                try:
                    h = CHMAC(key, SHA256())
                    h.update(compressed)
                    h.verify(stored_hmac)
                except Exception:
                    continue  # Wrong offsets, try next

                # Decompress
                try:
                    raw = lz4.block.decompress(compressed, uncompressed_size=uncomp)
                    return raw
                except Exception:
                    try:
                        raw = lz4.block.decompress(compressed)
                        return raw
                    except Exception:
                        continue

    raise ValueError(f"Could not decrypt save file - no valid offset combination found (file={file_size}, payload={payload_size})")


# --- PARC parser ---

def read_str(data, pos):
    """Read a length-prefixed string (4-byte LE length)."""
    if pos + 4 > len(data): return None, pos
    slen = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    if pos + slen > len(data): return None, pos
    s = data[pos:pos + slen].decode('utf-8', errors='replace')
    pos += slen
    return s, pos

def parse_parc_schema(data, offset):
    """Parse the PARC schema section to extract type definitions."""
    magic = struct.unpack_from('<H', data, offset)[0]
    if magic != 0xFFFF:
        raise ValueError(f"Bad PARC magic: {hex(magic)} at offset {offset}")
    pos = offset + 2

    num_types = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    # Skip padding/reserved bytes until we hit the first type
    # Look for the pattern: field_count(4) + separator(2) + string_len(4) + string
    # The first type starts with its field count

    # Actually, bytes 6-13 appear to be padding (8 zero bytes)
    pos += 8  # skip padding

    types = []
    for i in range(num_types):
        if pos + 4 > len(data): break

        # Number of fields in this type
        num_fields = struct.unpack_from('<I', data, pos)[0]
        pos += 4

        # Separator byte(s)
        if pos < len(data) and data[pos] == 0x5f:
            # 0x5f = '_', means the type name starts with underscore
            # Actually this is part of the first field name
            pass
        else:
            # Skip separator
            sep = struct.unpack_from('<H', data, pos)[0]
            pos += 2

        # Read type name
        type_name, pos = read_str(data, pos)
        if type_name is None: break

        fields = []
        for j in range(num_fields):
            if pos + 4 > len(data): break

            # Field name
            field_name, pos = read_str(data, pos)
            if field_name is None: break

            # Field type
            field_type, pos = read_str(data, pos)
            if field_type is None: break

            # Field metadata: kind(1) + size(2) + aux(2) = 5 bytes
            if pos + 5 > len(data): break
            meta_kind = data[pos]
            pos += 1
            meta_size = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            meta_aux = struct.unpack_from('<H', data, pos)[0]
            pos += 2

            fields.append({
                'name': field_name,
                'type': field_type,
                'meta_kind': meta_kind,
                'meta_size': meta_size,
                'meta_aux': meta_aux
            })

        types.append({
            'name': type_name,
            'fields': fields
        })

    return types, pos


def parse_parc_toc(data, offset):
    """Parse the Table of Contents section."""
    num_entries = struct.unpack_from('<I', data, offset)[0]
    offset += 4

    entries = []
    for i in range(num_entries):
        class_index = struct.unpack_from('<I', data, offset)[0]
        sentinel = struct.unpack_from('<I', data, offset + 4)[0]
        data_offset = struct.unpack_from('<I', data, offset + 8)[0]
        data_size = struct.unpack_from('<I', data, offset + 12)[0]
        extra = struct.unpack_from('<I', data, offset + 16)[0]
        entries.append({
            'class_index': class_index,
            'sentinel': sentinel,
            'data_offset': data_offset,
            'data_size': data_size,
            'extra': extra
        })
        offset += 20

    return entries, offset


def explore_save(filepath):
    """Decrypt a save file and return schema + TOC for exploration."""
    raw = decrypt_save(filepath)
    print(f"Decrypted: {len(raw)} bytes")

    try:
        schema, schema_end = parse_parc_schema(raw, 0)
        print(f"Schema: {len(schema)} types")
        toc, toc_end = parse_parc_toc(raw, schema_end)
        print(f"TOC: {len(toc)} entries")
        return raw, schema, toc
    except Exception as e:
        print(f"PARC parse error: {e}")
        # Dump first 200 bytes for debugging
        print(f"First 64 bytes: {raw[:64].hex()}")
        print(f"Readable: {''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[:200])}")
        return raw, None, None


def find_save_dir():
    """Find the Crimson Desert save directory."""
    base = os.path.expandvars(r'%LOCALAPPDATA%\Pearl Abyss\CD\save')
    if not os.path.exists(base):
        return None
    # Find the steam ID subdirectory
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and d.isdigit():
            return full
    return base


def list_save_slots(save_dir):
    """List available save slots with timestamps."""
    slots = []
    for d in sorted(os.listdir(save_dir)):
        save_file = os.path.join(save_dir, d, 'save.save')
        if os.path.exists(save_file):
            mtime = os.path.getmtime(save_file)
            size = os.path.getsize(save_file)
            from datetime import datetime
            ts = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            slots.append({'slot': d, 'path': save_file, 'time': ts, 'size': size})
    return slots


if __name__ == '__main__':
    save_dir = find_save_dir()
    if not save_dir:
        print("Could not find Crimson Desert save directory")
        sys.exit(1)

    print(f"Save directory: {save_dir}")
    slots = list_save_slots(save_dir)
    print(f"\nAvailable slots:")
    for s in slots:
        print(f"  {s['slot']}: {s['time']} ({s['size'] // 1024} KB)")

    # Use most recent slot by default, or specified slot
    slot = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list-classes':
            # Decrypt and list all class names in the schema
            newest = max(slots, key=lambda s: s['time'])
            print(f"\nDecrypting {newest['slot']}...")
            raw, schema, toc = explore_save(newest['path'])
            if schema:
                print(f"\n=== ALL CLASSES ({len(schema)}) ===")
                for i, t in enumerate(schema):
                    fields_str = ', '.join(f['name'] for f in t['fields'][:5])
                    if len(t['fields']) > 5:
                        fields_str += f', ... (+{len(t["fields"]) - 5} more)'
                    print(f"  [{i}] {t['name']} ({len(t['fields'])} fields): {fields_str}")

                # Save schema to file
                out_path = os.path.join(os.path.dirname(__file__), '..', 'save_schema.json')
                with open(out_path, 'w') as f:
                    json.dump(schema, f, indent=2)
                print(f"\nSchema saved to {out_path}")
            sys.exit(0)

        slot = sys.argv[1]

    if not slot:
        # Use most recent
        newest = max(slots, key=lambda s: s['time'])
        slot = newest['slot']

    save_path = os.path.join(save_dir, slot, 'save.save')
    if not os.path.exists(save_path):
        print(f"Save file not found: {save_path}")
        sys.exit(1)

    print(f"\nDecrypting {slot}/save.save...")
    raw, schema, toc = explore_save(save_path)

    if schema:
        # Find interesting classes
        interesting = ['quest', 'item', 'inventory', 'time', 'knowledge',
                       'faction', 'discover', 'progress', 'collect', 'mission',
                       'world', 'save', 'character', 'player']
        print(f"\n=== INTERESTING CLASSES ===")
        for i, t in enumerate(schema):
            name_lower = t['name'].lower()
            if any(k in name_lower for k in interesting):
                print(f"  [{i}] {t['name']} ({len(t['fields'])} fields)")
                for f in t['fields']:
                    print(f"      .{f['name']} : {f['type']} (kind={f['meta_kind']})")
