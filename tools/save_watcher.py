"""
Crimson Desert Save Watcher
Reads save files to extract game progress and outputs JSON for the interactive map.

Watches for save file changes and auto-updates progress.

Usage:
  python tools/save_watcher.py              # One-shot: read latest save, output progress
  python tools/save_watcher.py --watch      # Watch for changes and auto-update
  python tools/save_watcher.py --slot slot0  # Read specific slot
  python tools/save_watcher.py --dump-schema # Dump all class/field names
"""

import sys
import os
import json
import time
import struct
import argparse

# Add NattKh's modules to path
CDMODS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'tmp', 'cdmods', 'CrimsonGameMods')
if not os.path.exists(CDMODS_PATH):
    CDMODS_PATH = 'C:/msys64/tmp/cdmods/CrimsonGameMods'
sys.path.insert(0, CDMODS_PATH)

from save_crypto import load_save_file
from parc_serializer import parse_parc_blob, BlockParser


def find_save_dir():
    base = os.path.expandvars(r'%LOCALAPPDATA%\Pearl Abyss\CD\save')
    if not os.path.exists(base):
        return None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and d.isdigit():
            return full
    return None


def list_slots(save_dir):
    slots = []
    for d in sorted(os.listdir(save_dir)):
        sf = os.path.join(save_dir, d, 'save.save')
        if os.path.exists(sf):
            slots.append({'slot': d, 'path': sf, 'mtime': os.path.getmtime(sf), 'size': os.path.getsize(sf)})
    return slots


def load_and_parse(save_path):
    """Load, decrypt, and parse a save file. Returns (parc, parser)."""
    sd = load_save_file(save_path)
    parc = parse_parc_blob(bytes(sd.decompressed_blob))
    parser = BlockParser(parc)
    return parc, parser


def extract_discovered(parc, parser):
    """Extract discovered location gimmick IDs from the save."""
    discovered = []
    # Find DiscoveredLevelGimmickSceneObjectSaveData (type index 86)
    # and LevelGimmickSceneObjectElementSaveData (type index 12)

    # Find the type indices
    disc_type_idx = None
    elem_type_idx = None
    for i, t in enumerate(parc.types):
        if t.name == 'DiscoveredLevelGimmickSceneObjectSaveData':
            disc_type_idx = i
        if t.name == 'LevelGimmickSceneObjectElementSaveData':
            elem_type_idx = i

    if elem_type_idx is None:
        return discovered

    # Parse all TOC entries and look for the discovered data
    elem_type = parc.types[elem_type_idx]

    for entry_idx, entry in enumerate(parc.toc_entries):
        if entry.class_index == (disc_type_idx if disc_type_idx is not None else -1):
            try:
                block = parser.parse_root_block(entry_idx)
                if block and '_discoveredLevelGimmickSceneObjectSaveDataList' in block:
                    items = block['_discoveredLevelGimmickSceneObjectSaveDataList']
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                key = item.get('_levelGimmickSceneObjectInfoKey', '')
                                completed = item.get('_isCompleted', False)
                                found = item.get('_isDiscoverd', False)
                                discovered.append({
                                    'key': str(key),
                                    'completed': bool(completed),
                                    'discovered': bool(found)
                                })
            except Exception as e:
                print(f"  Warning: could not parse entry {entry_idx}: {e}", file=sys.stderr)

    return discovered


def extract_bank_history(parc, parser):
    """Extract bank investment history/timers."""
    bank_data = []

    # Find InventoryItemContentsSaveData_BankHistoryData
    bank_type_idx = None
    inv_type_idx = None
    for i, t in enumerate(parc.types):
        if t.name == 'InventoryItemContentsSaveData_BankHistoryData':
            bank_type_idx = i
        if t.name == 'InventoryItemContentsSaveData':
            inv_type_idx = i

    if inv_type_idx is None:
        return bank_data

    for entry_idx, entry in enumerate(parc.toc_entries):
        if entry.class_index == inv_type_idx:
            try:
                block = parser.parse_root_block(entry_idx)
                if block:
                    last_update = block.get('_lastUpdateBankTime', 0)
                    propensity = block.get('_investmentPropensity', 0)
                    history = block.get('_bankHistoryDataList', [])

                    bank_data.append({
                        'lastUpdateBankTime': last_update,
                        'investmentPropensity': propensity,
                        'historyCount': len(history) if isinstance(history, list) else 0,
                        'history': []
                    })

                    if isinstance(history, list):
                        for h in history:
                            if isinstance(h, dict):
                                bank_data[-1]['history'].append({
                                    'updateTime': h.get('_updateHistoryTime', 0),
                                    'applyPercent': h.get('_applyPercent', 0),
                                    'currentMoney': h.get('_currentDefaultMoneyCount', 0),
                                    'prevMoney': h.get('_prevDefaultMoneyCount', 0),
                                    'isBenefit': h.get('_isBenefit', False)
                                })
            except Exception as e:
                print(f"  Warning: could not parse inventory entry {entry_idx}: {e}", file=sys.stderr)

    return bank_data


def extract_quests(parc, parser):
    """Extract quest completion states."""
    quests = []

    quest_type_idx = None
    stage_type_idx = None
    mission_type_idx = None
    for i, t in enumerate(parc.types):
        if t.name == 'QuestSaveData':
            quest_type_idx = i
        if t.name == 'StageStateData':
            stage_type_idx = i
        if t.name == 'MissionStateData':
            mission_type_idx = i

    if quest_type_idx is None:
        return quests

    for entry_idx, entry in enumerate(parc.toc_entries):
        if entry.class_index == quest_type_idx:
            try:
                block = parser.parse_root_block(entry_idx)
                if block:
                    stages = block.get('_stageStateData', [])
                    missions = block.get('_missionStateList', [])
                    quest_states = block.get('_questStateList', [])

                    if isinstance(stages, list):
                        for s in stages:
                            if isinstance(s, dict):
                                quests.append({
                                    'type': 'stage',
                                    'key': str(s.get('_key', '')),
                                    'state': s.get('_state', 0),
                                    'completedCount': s.get('_completedCount', 0)
                                })

                    if isinstance(quest_states, list):
                        for q in quest_states:
                            if isinstance(q, dict):
                                quests.append({
                                    'type': 'quest',
                                    'key': str(q.get('_questKey', '')),
                                    'state': q.get('_state', 0)
                                })
            except Exception as e:
                print(f"  Warning: could not parse quest entry {entry_idx}: {e}", file=sys.stderr)

    return quests


def extract_character(parc, parser):
    """Extract character stats."""
    for entry_idx, entry in enumerate(parc.toc_entries):
        if entry.class_index == 0:  # CharacterStatusSaveData is always first
            try:
                block = parser.parse_root_block(entry_idx)
                if block:
                    return {
                        'level': block.get('_level', 0),
                        'experience': block.get('_experience', 0),
                        'characterKey': str(block.get('_characterKey', '')),
                        'factionKey': str(block.get('_factionKey', ''))
                    }
            except Exception as e:
                pass
    return None


def extract_position(parc, parser):
    """Extract last known player position."""
    tf_type_idx = None
    for i, t in enumerate(parc.types):
        if t.name == 'TransformFieldSaveData':
            tf_type_idx = i
            break

    if tf_type_idx is None:
        return None

    for entry_idx, entry in enumerate(parc.toc_entries):
        if entry.class_index == tf_type_idx:
            try:
                block = parser.parse_root_block(entry_idx)
                if block:
                    return {
                        'fieldInfoKey': str(block.get('_fieldInfoKey', '')),
                        'position': block.get('_position', None),
                        'rotation': block.get('_rotation', None)
                    }
            except Exception as e:
                pass
    return None


def extract_all(save_path):
    """Extract all useful data from a save file."""
    print(f"Reading: {save_path}")
    parc, parser = load_and_parse(save_path)
    print(f"  Parsed: {len(parc.types)} types, {len(parc.toc_entries)} TOC entries")

    result = {
        'savePath': save_path,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'character': extract_character(parc, parser),
        'discovered': extract_discovered(parc, parser),
        'bankHistory': extract_bank_history(parc, parser),
        'quests': extract_quests(parc, parser),
    }

    print(f"  Character: {result['character']}")
    print(f"  Discovered locations: {len(result['discovered'])}")
    print(f"  Bank entries: {sum(b['historyCount'] for b in result['bankHistory'])}")
    print(f"  Quest entries: {len(result['quests'])}")

    return result


def main():
    ap = argparse.ArgumentParser(description='Crimson Desert Save Watcher')
    ap.add_argument('--slot', default=None, help='Specific slot to read (e.g. slot0)')
    ap.add_argument('--watch', action='store_true', help='Watch for save changes')
    ap.add_argument('--interval', type=int, default=5, help='Watch interval in seconds')
    ap.add_argument('--output', default=None, help='Output JSON file path')
    ap.add_argument('--dump-schema', action='store_true', help='Dump all type/field names')
    args = ap.parse_args()

    save_dir = find_save_dir()
    if not save_dir:
        print("Could not find save directory")
        sys.exit(1)

    slots = list_slots(save_dir)
    if not slots:
        print("No save slots found")
        sys.exit(1)

    # Pick slot
    if args.slot:
        slot = next((s for s in slots if s['slot'] == args.slot), None)
        if not slot:
            print(f"Slot {args.slot} not found. Available: {[s['slot'] for s in slots]}")
            sys.exit(1)
    else:
        slot = max(slots, key=lambda s: s['mtime'])

    print(f"Using: {slot['slot']} (modified {time.ctime(slot['mtime'])})")

    if args.dump_schema:
        parc, parser = load_and_parse(slot['path'])
        for i, t in enumerate(parc.types):
            print(f"\n[{i}] {t.name}")
            for f in t.fields:
                print(f"    .{f.name} : {f.type_name} (kind={f.meta_kind}, size={f.meta_size})")
        sys.exit(0)

    output_path = args.output or os.path.join(os.path.dirname(__file__), '..', 'save_progress.json')

    if args.watch:
        print(f"Watching for changes every {args.interval}s... (Ctrl+C to stop)")
        last_mtime = 0
        while True:
            current_mtime = os.path.getmtime(slot['path'])
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                try:
                    result = extract_all(slot['path'])
                    with open(output_path, 'w') as f:
                        json.dump(result, f, indent=2, default=str)
                    print(f"  -> Written to {output_path}")
                except Exception as e:
                    print(f"  Error: {e}")
            time.sleep(args.interval)
    else:
        result = extract_all(slot['path'])
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nWritten to {output_path}")


if __name__ == '__main__':
    main()
