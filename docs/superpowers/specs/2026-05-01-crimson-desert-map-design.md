# Crimson Desert Interactive Map — Design Spec

## Overview

A standalone interactive map application for Crimson Desert. Replicates MapGenie's full feature set (category groups, progress tracking, search, filtering) without requiring a server or account. Progress stored in localStorage with JSON file backup. Designed for sharing with others — zip the folder and send.

## Goals

- Full MapGenie-style category system with collapsible groups, per-category toggles, and progress tracking
- Pre-populated marker database with ability to add custom markers on top
- localStorage progress tracking that survives reboots
- JSON export/import for backup and sharing
- Multi-map support (world map, dungeons, etc.)
- Architecture ready for a future save file parser plug-in
- Shareable: zip the folder and send to anyone — works offline from `file://`

## Architecture

### File Structure

```
crimson_desert_map/
├── index.html              # App entry point (UI + inline JS/CSS)
├── lib/
│   ├── leaflet.js          # Leaflet bundled locally (no CDN dependency)
│   └── leaflet.css
├── data/
│   ├── maps.js             # Map registry as JS (window.CDM_MAPS = [...])
│   ├── markers/
│   │   ├── the-continent.js    # window.CDM_MARKERS["the-continent"] = {...}
│   │   ├── dungeons.js
│   │   └── ...
│   └── images/
│       ├── the-continent.jpg
│       ├── dungeons.jpg
│       └── ...
└── saves/                  # Future: save parser output directory
```

### Technology

- **Leaflet.js** bundled locally in `lib/` — no CDN, works offline from `file://`
- **Vanilla JS** — no framework, no build step
- **CSS** — inline in `index.html`, dark theme to match game aesthetic
- **localStorage** — progress persistence
- **File API** — JSON export/import

### Why This Approach

- No npm, no build tools, no server required
- Share by zipping the folder — opens directly from `file://` in any browser
- Marker data files are `.js` (not `.json`) loaded via `<script>` tags — avoids `fetch()` which is blocked on `file://`
- Marker data and map images are separate files so the database can be updated independently

### Data Loading (file:// Compatible)

Since `fetch()` is blocked on `file://`, all data files are `.js` files that register themselves on `window`:

```html
<!-- index.html loads data via script tags -->
<script src="data/maps.js"></script>
<script src="data/markers/the-continent.js"></script>
<!-- App code reads window.CDM_MAPS, window.CDM_MARKERS["the-continent"] -->
```

`index.html` dynamically creates `<script>` tags when switching maps to load marker data on demand.

## Data Model

### Map Registry (`data/maps.js`)

```js
window.CDM_MAPS = [
  {
    "id": "the-continent",
    "title": "The Continent",
    "image": "data/images/the-continent.jpg",
    "markersFile": "data/markers/the-continent.js",
    "bounds": [[0, 0], [1000, 1000]],
    "imageSize": [4096, 4096]
  },
  {
    "id": "dungeon-a",
    "title": "Some Dungeon",
    "image": "data/images/dungeon-a.jpg",
    "markersFile": "data/markers/dungeon-a.js",
    "bounds": [[0, 0], [500, 500]],
    "imageSize": [2048, 2048]
  }
];
```

- `bounds` defines the coordinate space for the image overlay (Leaflet CRS.Simple)
- `imageSize` is the actual pixel dimensions of the map image — coordinates map 1:1 to image pixels
- `image` and `markersFile` are paths relative to `index.html`

### Marker Data (`data/markers/<map-id>.js`)

```js
window.CDM_MARKERS = window.CDM_MARKERS || {};
window.CDM_MARKERS["the-continent"] = {
  "schemaVersion": 1,
  "groups": [
    {
      "id": "locations",
      "title": "Locations",
      "color": "#8B4513",
      "categories": [
        {
          "id": "fast-travel",
          "title": "Fast Travel",
          "icon": "fast-travel"
        },
        {
          "id": "boss",
          "title": "Boss",
          "icon": "boss"
        }
      ]
    },
    {
      "id": "collectibles",
      "title": "Collectibles",
      "color": "#DAA520",
      "categories": [
        {
          "id": "chest",
          "title": "Chest",
          "icon": "chest"
        }
      ]
    }
  ],
  "markers": [
    {
      "id": "ft-001",
      "categoryId": "fast-travel",
      "title": "Lunaris Waypoint",
      "description": "Near the northern bridge",
      "x": 340.2,
      "y": 120.5
    }
  ]
};
```

- Each marker has a unique `id` within its map
- `categoryId` links to a category defined in `groups`
- **`x`/`y` are image pixel coordinates** — `x` is horizontal (left-to-right), `y` is vertical (top-to-bottom). Mapped to Leaflet as `L.latLng(y, x)` since CRS.Simple treats lat as vertical axis
- `schemaVersion` enables future migration of marker data format
- Icons are CSS classes or emoji — no external icon sprites needed initially

### Progress Data (localStorage, key: `cdm-progress`)

```json
{
  "schemaVersion": 1,
  "the-continent": {
    "found": ["ft-001", "boss-003"],
    "notes": {
      "ft-001": "Unlocked after Chapter 2"
    },
    "customMarkers": [
      {
        "id": "custom-1716000000000",
        "categoryId": "custom",
        "isCustom": true,
        "title": "My spot",
        "x": 200,
        "y": 50,
        "note": "Good farming location"
      }
    ]
  },
  "dungeon-a": {
    "found": ["chest-010"],
    "notes": {},
    "customMarkers": []
  }
}
```

- `schemaVersion` at the root — enables migration when format changes
- Progress is keyed by map ID — each map tracks independently
- `found` is an array of marker IDs (from pre-populated data only)
- `notes` is a map of marker ID → user note text
- `customMarkers` have `isCustom: true` to distinguish from pre-populated markers
- Custom markers are **excluded from progress totals** — only pre-populated markers count toward completion %
- This entire object is what gets exported/imported as JSON backup

### Separation of Concerns

| Data | Storage | Shareable? |
|------|---------|------------|
| Marker database | `data/markers/*.js` files | Yes — share the whole `data/` folder |
| Map images | `data/images/*.jpg` files | Yes — included in the zip |
| User progress | localStorage + JSON export | Per-user, export to share |
| Custom markers | Inside progress data | Per-user |

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Crimson Desert Map]  [Map Selector ▼]  [+ Add] [⚙]   │
├──────────────┬──────────────────────────────────────────┤
│  Sidebar     │                                          │
│  ┌────────┐  │                                          │
│  │🔍Search│  │                                          │
│  ├────────┤  │           Map Canvas                     │
│  │▼ Locations│           (Leaflet)                      │
│  │  ☑ Fast T.│                                          │
│  │  ☐ Boss   │              ● marker                    │
│  │▼ Collecti.│                    ● marker              │
│  │  ☑ Chest  │                                          │
│  │  ☑ Relic  │                                          │
│  ├────────┤  │                                          │
│  │Progress│  │                                          │
│  │████░ 62%│  │                                          │
│  └────────┘  │                                          │
├──────────────┴──────────────────────────────────────────┤
│  Total: 245/394 found                                   │
└─────────────────────────────────────────────────────────┘
```

### Sidebar

- **Search box** — filters markers by title within visible (checked) categories. Non-matching markers dim to 20% opacity on the map. Category toggle takes precedence over search — if a category is unchecked, its markers stay hidden regardless of search matches
- **Category groups** — collapsible. Click group header to expand/collapse. Each category has a checkbox to toggle visibility on the map
- **Per-category progress** — `3/12` found count next to each category name (pre-populated markers only)
- **Overall progress** — bar + percentage at the bottom of the sidebar (pre-populated markers only)

### Top Bar

- **Title** — "Crimson Desert Map"
- **Map selector** — dropdown to switch between maps. Switching loads new marker data + map image, preserves progress
- **Add Marker button (+)** — opens "Add Custom Marker" mode (click map to place). Works on both desktop and mobile (alternative to right-click)
- **Tools menu (⚙)** — Export Progress, Import Progress, Import Save (future), Reset Progress, Export Marker Data

### Status Bar

- Total found count across all categories on the current map (pre-populated only)

### Filter Precedence

Visibility is determined by this priority chain (highest first):
1. **Category toggle** — unchecked = always hidden, no exceptions
2. **Search filter** — within visible categories, non-matching markers dim to 20% opacity
3. **Found state** — found markers show at 50% opacity with checkmark overlay (applied on top of search dimming)

## Marker Interactions

### Click Pre-populated Marker → Info Popup

```
┌──────────────────────┐
│ Lunaris Waypoint      │
│ Category: Fast Travel │
│ Near the northern     │
│ bridge                │
│                       │
│ Notes: [          ]   │
│                       │
│ [✓ Mark Found]        │
└──────────────────────┘
```

- **Mark Found** toggles found/unfound state
- **Notes** text field — auto-saves to localStorage on blur
- Pre-populated markers cannot be deleted or moved
- All text rendered via `textContent` — never `innerHTML` (prevents XSS from shared marker data or imported notes)

### Found Marker Appearance

- Green checkmark overlay on the marker icon
- 50% opacity
- Visually distinct from unfound markers at a glance

### Adding Custom Markers

Two methods (both work on desktop and mobile):

1. **Toolbar button** — click "+" in top bar, then click map to place
2. **Right-click** — right-click empty map space (desktop only)

Both open the same popup:

```
┌──────────────────────┐
│ Add Custom Marker     │
│ Title: [          ]   │
│ Category: [Select ▼]  │
│ Note: [           ]   │
│ [Add]  [Cancel]       │
└──────────────────────┘
```

- Category dropdown lists all existing categories + a "Custom" option
- Custom markers get a visually distinct style (dashed border or diamond shape)
- Custom markers can be edited (click → popup with Edit/Delete buttons)
- Custom markers can be dragged to reposition
- Custom markers are **not counted** in category or overall progress totals

### Search Behavior

- Typing in search box filters within currently visible (checked) categories
- On the map, non-matching markers dim to 20% opacity
- Matching markers pulse or highlight briefly
- Clear search restores all visibility
- Search does not override category toggles — hidden categories stay hidden

## Tools / Import-Export

### Export Progress

- Downloads a `crimson-desert-progress-YYYY-MM-DD.json` file
- Contains the full progress object (found markers, notes, custom markers) for all maps
- Timestamped filename prevents accidental overwrites

### Import Progress

- File picker for `.json` files
- Validates format and `schemaVersion` before importing
- Asks: "Merge with existing progress or replace?"
  - **Merge** — union of found marker IDs, keeps newer notes on conflict, appends custom markers (deduped by ID)
  - **Replace** — overwrites all progress
- Unknown marker IDs (not in current marker data) are preserved silently — they may belong to a newer version of the marker database

### Export Marker Data

- Downloads the current map's marker data as a `.js` file
- Allows sharing the marker database separately from progress
- Recipients drop the file into their `data/markers/` folder

### Import Save (Future)

- File picker to select a `parsed.json` file
- Same merge/replace flow as Import Progress
- Parser interface contract:

```json
{
  "parsedAt": "2026-05-01T12:00:00Z",
  "mapId": "the-continent",
  "found": ["ft-001", "chest-042"]
}
```

### Reset Progress

- Confirmation dialog: "Reset all progress for [current map] or all maps?"
- Three options: "This Map" / "All Maps" / "Cancel"

## Visual Design

- **Dark theme** — dark background (#1a1a2e or similar), light text, matches game aesthetic
- **Color-coded groups** — each group header has its configured color
- **Marker icons** — simple colored circles with category initials initially. Can be upgraded to custom SVG icons later
- **Responsive** — sidebar collapses to hamburger menu on narrow screens
- **All user-controlled text** (descriptions, notes, imported content) rendered via `textContent`, never `innerHTML`

## Future Save Parser Plug-in Architecture

The app exposes a simple contract for save parsing:

1. An external tool (Python script, Rust CLI, etc.) reads Crimson Desert save files from `C:/Users/<user>/AppData/Local/Pearl Abyss/CD/save/<steamId>/`
2. Save files are proprietary binary (`.save` format with `SAVE` magic header, encrypted/compressed body)
3. The parser outputs `saves/parsed.json` matching the import format above
4. The user clicks "Import Save" in the app to load it
5. Later enhancement: if served from a local HTTP server, the app could poll `saves/parsed.json` and auto-import on change

The parser is a completely separate project — the map app just consumes its output.

## What's NOT in Scope

- User accounts or authentication
- Server-side storage
- Real-time multiplayer/sync
- Tile-based map rendering (using single image overlay — acceptable unless map images exceed ~8K resolution)
- Mobile-native app (web-only, but responsive)
- Reverse engineering the `.save` file format (separate future project)
- Detailed error UX — v1 uses `console.warn` + silent fallbacks for missing data, storage errors, etc.
