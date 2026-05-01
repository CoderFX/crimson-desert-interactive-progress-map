# Crimson Desert Interactive Map — Design Spec

## Overview

A standalone, single-file interactive map application for Crimson Desert. Replicates MapGenie's full feature set (category groups, progress tracking, search, filtering) without requiring a server or account. Progress stored in localStorage with JSON file backup. Designed for sharing with others.

## Goals

- Full MapGenie-style category system with collapsible groups, per-category toggles, and progress tracking
- Pre-populated marker database with ability to add custom markers on top
- localStorage progress tracking that survives reboots
- JSON export/import for backup and sharing
- Multi-map support (world map, dungeons, etc.)
- Architecture ready for a future save file parser plug-in
- Shareable: zip the folder and send to anyone

## Architecture

### File Structure

```
crimson_desert_map/
├── index.html              # Single-file app (Leaflet + all UI + JS inline)
├── data/
│   ├── maps.json           # Map registry (list of maps + metadata)
│   ├── markers/
│   │   ├── the-continent.json
│   │   ├── dungeons.json
│   │   └── ...             # One file per map region
│   └── images/
│       ├── the-continent.jpg
│       ├── dungeons.jpg
│       └── ...             # One map image per map
└── saves/                  # Future: save parser output directory
```

### Technology

- **Leaflet.js** via CDN — map rendering, markers, popups
- **Vanilla JS** — no framework, no build step
- **CSS** — inline in `index.html`, dark theme to match game aesthetic
- **localStorage** — progress persistence
- **File API** — JSON export/import

### Why Single File

- No npm, no build tools, no server
- Share by zipping the folder
- Opens in any browser (Chrome, Brave, Firefox, Edge)
- Marker data and map images are separate files so the database can be updated independently

## Data Model

### Map Registry (`data/maps.json`)

```json
[
  {
    "id": "the-continent",
    "title": "The Continent",
    "image": "images/the-continent.jpg",
    "markers": "markers/the-continent.json",
    "bounds": [[0, 0], [1000, 1000]]
  },
  {
    "id": "dungeon-a",
    "title": "Some Dungeon",
    "image": "images/dungeon-a.jpg",
    "markers": "markers/dungeon-a.json",
    "bounds": [[0, 0], [500, 500]]
  }
]
```

- `bounds` defines the coordinate space for the image overlay (Leaflet CRS.Simple)
- `image` and `markers` are paths relative to `data/`

### Marker Data (`data/markers/<map-id>.json`)

```json
{
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
      "lat": 120.5,
      "lng": 340.2
    }
  ]
}
```

- Each marker has a unique `id` within its map
- `categoryId` links to a category defined in `groups`
- `lat`/`lng` are pixel coordinates in Leaflet's CRS.Simple coordinate system
- Icons are CSS classes or emoji — no external icon sprites needed initially

### Progress Data (localStorage, key: `cdm-progress`)

```json
{
  "the-continent": {
    "found": ["ft-001", "boss-003"],
    "notes": {
      "ft-001": "Unlocked after Chapter 2"
    },
    "customMarkers": [
      {
        "id": "custom-1716000000000",
        "categoryId": "custom",
        "title": "My spot",
        "lat": 50,
        "lng": 200,
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

- Progress is keyed by map ID — each map tracks independently
- `found` is an array of marker IDs (from pre-populated data)
- `notes` is a map of marker ID → user note text
- `customMarkers` are user-added markers with timestamp-based IDs
- This entire object is what gets exported/imported as JSON backup

### Separation of Concerns

| Data | Storage | Shareable? |
|------|---------|------------|
| Marker database | `data/markers/*.json` files | Yes — share the whole `data/` folder |
| Map images | `data/images/*.jpg` files | Yes — included in the zip |
| User progress | localStorage + JSON export | Per-user, export to share |
| Custom markers | Inside progress data | Per-user |

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Crimson Desert Map]    [Map Selector ▼]    [⚙ Tools]  │
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

- **Search box** — filters markers by title. Matches show in sidebar AND on map (non-matching markers dim)
- **Category groups** — collapsible. Click group header to expand/collapse. Each category has a checkbox to toggle visibility on the map
- **Per-category progress** — `3/12` found count next to each category name
- **Overall progress** — bar + percentage at the bottom of the sidebar

### Top Bar

- **Title** — "Crimson Desert Map"
- **Map selector** — dropdown to switch between maps. Switching loads new marker data + map image, preserves progress
- **Tools menu (⚙)** — Export Progress, Import Progress, Import Save (future), Reset Progress, Share Marker Data

### Status Bar

- Total found count across all categories on the current map

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

### Found Marker Appearance

- Green checkmark overlay on the marker icon
- 50% opacity
- Visually distinct from unfound markers at a glance

### Right-Click Empty Map Space → Add Custom Marker

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

### Search Behavior

- Typing in search box filters sidebar categories to show only matching markers
- On the map, non-matching markers dim to 20% opacity
- Matching markers pulse or highlight briefly
- Clear search restores all visibility

## Tools / Import-Export

### Export Progress

- Downloads a `crimson-desert-progress-YYYY-MM-DD.json` file
- Contains the full progress object (found markers, notes, custom markers) for all maps
- Timestamped filename prevents accidental overwrites

### Import Progress

- File picker for `.json` files
- Validates format before importing
- Asks: "Merge with existing progress or replace?"
  - **Merge** — adds found markers and custom markers, preserves existing
  - **Replace** — overwrites all progress

### Import Save (Future)

- File picker or watch directory (`saves/`)
- Reads `saves/parsed.json` (output of future save parser)
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
- Two options: "This Map" / "All Maps" / "Cancel"

## Visual Design

- **Dark theme** — dark background (#1a1a2e or similar), light text, matches game aesthetic
- **Color-coded groups** — each group header has its configured color
- **Marker icons** — simple colored circles with category initials initially. Can be upgraded to custom SVG icons later
- **Responsive** — sidebar collapses to hamburger menu on narrow screens

## Future Save Parser Plug-in Architecture

The app exposes a simple contract for save parsing:

1. An external tool (Python script, Rust CLI, etc.) reads Crimson Desert save files
2. It writes `saves/parsed.json` matching the import format
3. The user clicks "Import Save" in the app to load it
4. Later enhancement: the app could poll `saves/parsed.json` via fetch and auto-import on change (when served from a local HTTP server)

The parser is a completely separate project — the map app just consumes its output.

## What's NOT in Scope

- User accounts or authentication
- Server-side storage
- Real-time multiplayer/sync
- Tile-based map rendering (using single image overlay)
- Mobile-native app (web-only, but responsive)
- Reverse engineering the `.save` file format (separate future project)
