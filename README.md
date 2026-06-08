# Crimson Desert Interactive Progress Map

A free, offline interactive map for **Crimson Desert** with full progress tracking. No account required, no server, no paywall. Just open `index.html` in your browser.


## Features

- **7,080 locations** across 116 categories (Strongholds, Collectibles, Quests, Bosses, Items, Resources, and more)
- **Pin icons** with unique category symbols matching the in-game style
- **Progress tracking** with localStorage persistence -- mark items as found, add notes
- **Full category system** -- collapsible groups, per-category toggles, group-level show/hide
- **Smart search** -- searches titles and descriptions, clickable results that pan to the marker
- **Internal cross-links** -- click linked locations in descriptions to jump between markers
- **Media images** in popups for 2,178 locations
- **Faction map overlay** toggle
- **Hide found markers** toggle with adjustable opacity slider
- **Custom markers** -- right-click or use the + button to add your own pins
- **Import/Export** progress as JSON for backup or sharing
- **Right-click category** to "show only this" for focused hunting
- **Responsive** -- works on mobile with collapsible sidebar
- **Live position tracking** -- shows your real-time location on the map (requires [CD Companion](https://www.nexusmods.com/crimsondesert/mods/2125))
- **Bank investment timers** -- track in-game investment returns with countdown alerts
- **Favorites system** -- star categories for quick access
- **One-click launcher** -- `start.bat` starts everything (map server + position tracker)
- **Fully offline** -- works from `file://`, no server needed

## Quick Start

### Recommended: Use the launcher (preserves progress across sessions)

1. [Download the ZIP](../../archive/refs/heads/master.zip) or clone the repo
2. Install [Python 3.13+](https://www.python.org/downloads/) if you don't have it
3. Double-click **`start.bat`**
4. The map opens at **http://localhost:8080** with live position tracking

`start.bat` launches an HTTP server on port 8080 and opens the map in your browser. Python is only needed for this — no other dependencies required.

> **Important:** Always use `http://localhost:8080` to keep your progress. Opening `index.html` directly via `file://` uses a different localStorage origin and your found items won't carry over.

### Simple: Just open the file

1. [Download the ZIP](../../archive/refs/heads/master.zip) or clone the repo
2. Open `index.html` in your browser (Chrome, Brave, Firefox, Edge)
3. That's it. No install, no build step, no server.

> Note: Progress saved this way won't be visible if you later switch to `start.bat`. Use the Export/Import feature to transfer.

## Usage Guide

### Tracking Progress

| Action | How |
|--------|-----|
| Mark as found | Click any marker, then click **Mark as Found** |
| Add a note | Click a marker, type in the **Notes** field |
| Hide found markers | Check **Hide found** in the sidebar header |
| Adjust found opacity | Drag the opacity slider in the sidebar header |

### Filtering

| Action | How |
|--------|-----|
| Hide a category | Uncheck its checkbox in the sidebar |
| Hide an entire group | Uncheck the group-level checkbox (e.g., uncheck "Resources") |
| Show only one category | **Right-click** any category name |
| Hide all categories | Click **Hide All** |
| Show all categories | Click **Show All** |
| Search for an item | Type in the search box (searches titles + descriptions) |

### Custom Markers

| Action | How |
|--------|-----|
| Add a custom marker | Click **+ Add** in the top bar, then click the map |
| Add via right-click | Right-click anywhere on the map |
| Move a custom marker | Drag it to a new position |
| Delete a custom marker | Click it, then click **Delete** |

### Import/Export

| Action | How |
|--------|-----|
| Export progress | Click the gear icon, then **Export Progress** |
| Import progress | Click the gear icon, then **Import Progress** |
| Export marker data | Click the gear icon, then **Export Marker Data** |
| Reset progress | Click the gear icon, then **Reset Progress** |

### Importing Existing Progress

If you have progress from another tracker, you can import it:

1. Create a JSON file matching the format in [`examples/example-progress.json`](examples/example-progress.json)
2. Import it via the gear icon > **Import Progress**
3. Choose **Merge** to combine with existing progress, or **Replace** to overwrite

### Faction Overlay

Click the **Factions** button in the top bar to toggle the faction territory overlay on the map.

## File Structure

```
crimson-desert-interactive-progress-map/
  start.bat               # Windows launcher (double-click to start everything)
  start.sh                # MSYS2/Git Bash launcher
  index.html              # The map app
  lib/
    leaflet.js            # Leaflet map library (bundled)
    leaflet.css
    fonts/                # Category icon font (icomoon)
    icons/                # 144 Metaforge PNG category icons
  data/
    maps.js               # Map configuration
    markers/
      pywel.js            # All 7,080 marker locations
    regions.js            # Region polygon boundaries
  tools/
    start_companion.py    # CD Companion position tracker bridge
    fetch-progress.js          # Helper to import progress from other trackers
    save_reader.py        # Crimson Desert save file decryptor (experimental)
    save_watcher.py       # Save file progress extractor (experimental)
  examples/
    example-progress.json # Example progress file format
```

## Data Storage

All progress is stored in your browser's `localStorage`:

| Key | What it stores |
|-----|---------------|
| `cdm-progress` | Found markers, notes, custom markers |
| `cdm-category-visibility` | Which categories are shown/hidden |
| `cdm-found-opacity` | Found marker opacity setting |
| `cdm-hide-found` | Whether found markers are hidden |
| `cdm-collapse` | Which sidebar groups are collapsed |

Your data stays on your machine. Nothing is sent anywhere.

## Sharing

**Share the map with friends:**
- Send them the ZIP file
- They open `index.html` and start their own progress from scratch

**Share your progress:**
- Export your progress JSON and send it to them
- They import it with merge or replace

**Share marker data updates:**
- Export marker data and share the `.js` file
- Recipients drop it into `data/markers/`

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `+` / `-` | Zoom in / out |
| Arrow keys | Pan the map |
| `Esc` | Close popup |

## Roadmap

- [x] Live position tracking via CD Companion WebSocket
- [x] Save file decryption (ChaCha20 + LZ4 + PARC format cracked)
- [x] Bank investment timers with in-game time conversion
- [x] Metaforge category icons (144 PNGs)
- [ ] Auto-track game progress from save files (PARC nested list parsing needed)
- [ ] Region-based navigation shortcuts (Hernand, Demeniss, Pailune, Delesyia, Abyss)
- [ ] Download map tiles locally for full offline support

## Prerequisites (for live tracking)

- [Python 3.13+](https://www.python.org/downloads/) with `pip install pymem websockets`
- [CD Companion](https://www.nexusmods.com/crimsondesert/mods/2125) source or the position tracker bridge in `tools/`
- Game must be running for position tracking to work

## Credits

- Map rendering by [Leaflet](https://leafletjs.com/)
- Category icons from [Metaforge](https://metaforge.app/crimson-desert/map/main)
- Position tracking based on [CD Companion](https://github.com/leandrodiogenes/cd-companion)
- Save file format research from [NattKh/CrimsonGameMods](https://github.com/NattKh/CRIMSON-DESERT-SAVE-EDITOR-AND-GAME-MODS) and [LukeFZ/pycrimson](https://github.com/LukeFZ/pycrimson)
- Location data sourced from community contributions

## License

This is a fan-made tool for personal use. Crimson Desert is developed by Pearl Abyss.
