# Crimson Desert Interactive Progress Map

A free, offline interactive map for **Crimson Desert** with full progress tracking. No account required, no server, no paywall. Just open `index.html` in your browser.

![Map Preview](https://cdn.mapgenie.io/images/games/crimson-desert/preview.jpg)

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
- **Fully offline** -- works from `file://`, no server needed

## Quick Start

1. [Download the ZIP](../../archive/refs/heads/master.zip) or clone the repo
2. Open `index.html` in your browser (Chrome, Brave, Firefox, Edge)
3. That's it. No install, no build step, no server.

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

### Importing from MapGenie

If you have existing progress on MapGenie, you can import it:

**Automatic (recommended):**

1. Go to [mapgenie.io/crimson-desert/maps/pywel](https://mapgenie.io/crimson-desert/maps/pywel) (logged in)
2. Open DevTools (F12) > Console
3. Paste the contents of [`tools/fetch-mapgenie-progress.js`](tools/fetch-mapgenie-progress.js) and press Enter
4. A `mapgenie-progress-YYYY-MM-DD.json` file downloads automatically
5. In the interactive map, click the gear icon > **Import Progress** and select the file

**Manual:**

1. On the MapGenie map page console, run: `copy(JSON.stringify(store.getState().user.foundLocations))`
2. Convert the IDs: each key like `"544020"` becomes `"loc-544020"`
3. Create a JSON file matching the format in [`examples/example-progress.json`](examples/example-progress.json)
4. Import it via the gear icon > **Import Progress**

### Faction Overlay

Click the **Factions** button in the top bar to toggle the faction territory overlay on the map.

## File Structure

```
crimson-desert-interactive-progress-map/
  index.html              # The app (open this in your browser)
  lib/
    leaflet.js            # Leaflet map library (bundled)
    leaflet.css
    fonts/
      icomoon.woff        # Category icon font
      icomoon.ttf
  data/
    maps.js               # Map configuration
    markers/
      pywel.js            # All 7,080 marker locations
  tools/
    fetch-mapgenie-progress.js  # Paste in MapGenie console to export progress
  examples/
    example-progress.json       # Example progress file format
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

- [ ] Auto-track game progress by reading game memory (save files are encrypted)
- [ ] Region-based navigation shortcuts (Hernand, Demeniss, Pailune, Delesyia, Abyss)
- [ ] Download map tiles locally for full offline support

## Credits

- Map tiles and location data sourced from [MapGenie](https://mapgenie.io/crimson-desert)
- Map rendering by [Leaflet](https://leafletjs.com/)
- Category icons from the Crimson Desert icon font

## License

This is a fan-made tool for personal use. Crimson Desert is developed by Pearl Abyss.
