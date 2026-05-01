# Crimson Desert Interactive Map — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, offline-capable interactive map for Crimson Desert with full category system, progress tracking, and import/export — no server required.

**Architecture:** Single `index.html` with inline JS/CSS, Leaflet bundled locally in `lib/`, marker data as `.js` files loaded via `<script>` tags (file:// compatible). Progress in localStorage with JSON file backup. Dark theme UI with collapsible sidebar.

**Tech Stack:** Leaflet.js (bundled), Vanilla JS (ES6), CSS (inline), localStorage, File API

---

## File Structure

```
crimson_desert_map/
├── index.html                          # App: all UI, CSS, JS inline
├── lib/
│   ├── leaflet.js                      # Leaflet 1.9.4 (minified)
│   └── leaflet.css                     # Leaflet styles
│   └── images/                         # Leaflet default marker images
│       ├── marker-icon.png
│       ├── marker-icon-2x.png
│       └── marker-shadow.png
├── data/
│   ├── maps.js                         # Map registry (window.CDM_MAPS)
│   ├── markers/
│   │   └── the-continent.js            # Starter marker data
│   └── images/
│       └── the-continent.jpg           # Placeholder map image
└── docs/                               # Specs and plans (already exists)
```

---

### Task 1: Scaffold Project and Bundle Leaflet

**Files:**
- Create: `lib/leaflet.js`
- Create: `lib/leaflet.css`
- Create: `lib/images/marker-icon.png`
- Create: `lib/images/marker-icon-2x.png`
- Create: `lib/images/marker-shadow.png`
- Create: `index.html` (minimal shell)

- [ ] **Step 1: Download Leaflet 1.9.4 and extract into lib/**

Run:
```bash
cd C:/msys64/home/gelum/crimson_desert_map
mkdir -p lib/images
curl -L "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" -o lib/leaflet.js
curl -L "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" -o lib/leaflet.css
curl -L "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png" -o lib/images/marker-icon.png
curl -L "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png" -o lib/images/marker-icon-2x.png
curl -L "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png" -o lib/images/marker-shadow.png
```

Expected: Five files downloaded into `lib/`.

- [ ] **Step 2: Create minimal index.html that loads Leaflet and shows a map**

Create `index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Crimson Desert Map</title>
  <link rel="stylesheet" href="lib/leaflet.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; background: #1a1a2e; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    #map { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: #16213e; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="lib/leaflet.js"></script>
  <script>
    // Fix Leaflet's default icon path for local files
    L.Icon.Default.imagePath = 'lib/images/';

    var map = L.map('map', {
      crs: L.CRS.Simple,
      minZoom: -2,
      maxZoom: 4,
      zoomControl: true
    });

    // Show a basic gray rectangle as placeholder
    var bounds = [[0, 0], [1000, 1000]];
    L.rectangle(bounds, { color: '#444', weight: 1, fillColor: '#2a2a4a', fillOpacity: 1 }).addTo(map);
    map.fitBounds(bounds);
  </script>
</body>
</html>
```

- [ ] **Step 3: Verify by opening in browser**

Run:
```bash
# On Windows, open in default browser
start "C:/msys64/home/gelum/crimson_desert_map/index.html"
```

Expected: Dark page with a gray/purple rectangle that can be panned and zoomed. Leaflet zoom controls visible.

- [ ] **Step 4: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add lib/ index.html
git commit -m "$(cat <<'EOF'
Scaffold project: bundle Leaflet locally, minimal index.html with CRS.Simple map
EOF
)"
```

---

### Task 2: Create Map Registry and Placeholder Map Image

**Files:**
- Create: `data/maps.js`
- Create: `data/images/the-continent.jpg` (placeholder)
- Create: `data/markers/the-continent.js` (empty starter)
- Modify: `index.html`

- [ ] **Step 1: Create a placeholder map image**

Run:
```bash
mkdir -p C:/msys64/home/gelum/crimson_desert_map/data/images
mkdir -p C:/msys64/home/gelum/crimson_desert_map/data/markers
```

Create a simple placeholder using Python (generates a 1024x1024 dark image with grid):
```bash
python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (1024, 1024), (26, 26, 46))
draw = ImageDraw.Draw(img)
for i in range(0, 1024, 64):
    draw.line([(i, 0), (i, 1024)], fill=(40, 40, 70), width=1)
    draw.line([(0, i), (1024, i)], fill=(40, 40, 70), width=1)
draw.text((400, 500), 'THE CONTINENT', fill=(100, 100, 140))
img.save('C:/msys64/home/gelum/crimson_desert_map/data/images/the-continent.jpg')
"
```

If Python/PIL not available, create a simple 1x1 pixel placeholder:
```bash
# Fallback: tiny JPEG placeholder
printf '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x27 ",#\x1c\x1c(7),01444\x1f\x27444444444444\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00T\xdb\x9e\xa7\xff\xd9' > "C:/msys64/home/gelum/crimson_desert_map/data/images/the-continent.jpg"
```

- [ ] **Step 2: Create data/maps.js**

Create `data/maps.js`:

```js
window.CDM_MAPS = [
  {
    id: "the-continent",
    title: "The Continent",
    image: "data/images/the-continent.jpg",
    markersFile: "data/markers/the-continent.js",
    bounds: [[0, 0], [1024, 1024]],
    imageSize: [1024, 1024]
  }
];
```

- [ ] **Step 3: Create data/markers/the-continent.js with sample markers**

Create `data/markers/the-continent.js`:

```js
window.CDM_MARKERS = window.CDM_MARKERS || {};
window.CDM_MARKERS["the-continent"] = {
  schemaVersion: 1,
  groups: [
    {
      id: "locations",
      title: "Locations",
      color: "#c0392b",
      categories: [
        { id: "fast-travel", title: "Fast Travel", icon: "FT" },
        { id: "boss", title: "Boss", icon: "B" }
      ]
    },
    {
      id: "collectibles",
      title: "Collectibles",
      color: "#f39c12",
      categories: [
        { id: "chest", title: "Chest", icon: "C" },
        { id: "relic", title: "Relic", icon: "R" }
      ]
    }
  ],
  markers: [
    { id: "ft-001", categoryId: "fast-travel", title: "Lunaris Waypoint", description: "Near the northern bridge", x: 300, y: 200 },
    { id: "ft-002", categoryId: "fast-travel", title: "Solaris Camp", description: "Southern desert outpost", x: 600, y: 700 },
    { id: "boss-001", categoryId: "boss", title: "Stone Guardian", description: "Level 15 boss, weak to fire", x: 500, y: 400 },
    { id: "chest-001", categoryId: "chest", title: "Hidden Chest", description: "Behind the waterfall", x: 150, y: 500 },
    { id: "chest-002", categoryId: "chest", title: "Buried Treasure", description: "Dig spot near the old tree", x: 800, y: 300 },
    { id: "relic-001", categoryId: "relic", title: "Ancient Tablet", description: "First piece of the prophecy", x: 450, y: 650 }
  ]
};
```

- [ ] **Step 4: Update index.html to load map data and show image overlay with markers**

Replace `index.html` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Crimson Desert Map</title>
  <link rel="stylesheet" href="lib/leaflet.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; background: #1a1a2e; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    #map { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: #16213e; }
  </style>
</head>
<body>
  <div id="map"></div>

  <script src="lib/leaflet.js"></script>
  <script src="data/maps.js"></script>
  <script src="data/markers/the-continent.js"></script>
  <script>
    // Fix Leaflet's default icon path for local files
    L.Icon.Default.imagePath = 'lib/images/';

    // --- App State ---
    var currentMapId = window.CDM_MAPS[0].id;
    var currentMapConfig = window.CDM_MAPS[0];
    var currentMarkerData = window.CDM_MARKERS[currentMapId];

    // --- Build category lookup ---
    var categoryMap = {};
    currentMarkerData.groups.forEach(function(group) {
      group.categories.forEach(function(cat) {
        categoryMap[cat.id] = { category: cat, group: group };
      });
    });

    // --- Create custom marker icon ---
    function createMarkerIcon(categoryId) {
      var info = categoryMap[categoryId];
      if (!info) return L.divIcon({ className: 'cdm-marker', html: '<div style="background:#888;width:24px;height:24px;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:bold;color:#fff;border:2px solid #fff;">?</div>', iconSize: [24, 24], iconAnchor: [12, 12] });
      var color = info.group.color;
      var icon = info.category.icon;
      return L.divIcon({
        className: 'cdm-marker',
        html: '<div style="background:' + color + ';width:24px;height:24px;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:bold;color:#fff;border:2px solid #fff;">' + icon + '</div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
    }

    // --- Init Map ---
    var map = L.map('map', {
      crs: L.CRS.Simple,
      minZoom: -2,
      maxZoom: 4,
      zoomControl: true
    });

    var bounds = currentMapConfig.bounds;
    L.imageOverlay(currentMapConfig.image, bounds).addTo(map);
    map.fitBounds(bounds);

    // --- Place markers ---
    currentMarkerData.markers.forEach(function(marker) {
      var latlng = L.latLng(marker.y, marker.x);
      var icon = createMarkerIcon(marker.categoryId);
      var leafletMarker = L.marker(latlng, { icon: icon }).addTo(map);
      leafletMarker.bindPopup(
        '<b>' + marker.title + '</b><br>' +
        '<small>' + (categoryMap[marker.categoryId] ? categoryMap[marker.categoryId].category.title : '') + '</small><br>' +
        (marker.description || '')
      );
    });
  </script>
</body>
</html>
```

- [ ] **Step 5: Open in browser and verify**

Run:
```bash
start "C:/msys64/home/gelum/crimson_desert_map/index.html"
```

Expected: Map shows placeholder image with 6 colored circle markers. Clicking a marker shows a popup with title, category, and description.

- [ ] **Step 6: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add data/ index.html
git commit -m "$(cat <<'EOF'
Add map registry, sample markers, and image overlay with marker rendering
EOF
)"
```

---

### Task 3: localStorage Progress Tracking

**Files:**
- Modify: `index.html` (add progress module and wire into marker popups)

- [ ] **Step 1: Add progress storage module to index.html**

Add this `<script>` block **before** the main app script (after the data script tags):

```html
<script>
// --- Progress Storage ---
var CDM_PROGRESS_KEY = 'cdm-progress';

var Progress = {
  _data: null,

  load: function() {
    try {
      var raw = localStorage.getItem(CDM_PROGRESS_KEY);
      this._data = raw ? JSON.parse(raw) : { schemaVersion: 1 };
    } catch (e) {
      console.warn('Failed to load progress, starting fresh:', e);
      this._data = { schemaVersion: 1 };
    }
    return this._data;
  },

  save: function() {
    try {
      localStorage.setItem(CDM_PROGRESS_KEY, JSON.stringify(this._data));
    } catch (e) {
      console.warn('Failed to save progress:', e);
    }
  },

  _ensureMap: function(mapId) {
    if (!this._data[mapId]) {
      this._data[mapId] = { found: [], notes: {}, customMarkers: [] };
    }
    return this._data[mapId];
  },

  isFound: function(mapId, markerId) {
    var mapData = this._data[mapId];
    return mapData ? mapData.found.indexOf(markerId) !== -1 : false;
  },

  toggleFound: function(mapId, markerId) {
    var mapData = this._ensureMap(mapId);
    var idx = mapData.found.indexOf(markerId);
    if (idx === -1) {
      mapData.found.push(markerId);
    } else {
      mapData.found.splice(idx, 1);
    }
    this.save();
    return idx === -1; // returns true if now found
  },

  getNote: function(mapId, markerId) {
    var mapData = this._data[mapId];
    return mapData && mapData.notes ? (mapData.notes[markerId] || '') : '';
  },

  setNote: function(mapId, markerId, text) {
    var mapData = this._ensureMap(mapId);
    if (text && text.trim()) {
      mapData.notes[markerId] = text.trim();
    } else {
      delete mapData.notes[markerId];
    }
    this.save();
  },

  getFoundCount: function(mapId, categoryId, allMarkers) {
    var mapData = this._data[mapId];
    if (!mapData) return { found: 0, total: 0 };
    var categoryMarkers = allMarkers.filter(function(m) { return m.categoryId === categoryId; });
    var foundCount = categoryMarkers.filter(function(m) { return mapData.found.indexOf(m.id) !== -1; }).length;
    return { found: foundCount, total: categoryMarkers.length };
  },

  getTotalCount: function(mapId, allMarkers) {
    var mapData = this._data[mapId];
    if (!mapData) return { found: 0, total: allMarkers.length };
    var foundCount = allMarkers.filter(function(m) { return mapData.found.indexOf(m.id) !== -1; }).length;
    return { found: foundCount, total: allMarkers.length };
  },

  getData: function() { return this._data; },

  getCustomMarkers: function(mapId) {
    var mapData = this._data[mapId];
    return mapData && mapData.customMarkers ? mapData.customMarkers : [];
  },

  addCustomMarker: function(mapId, marker) {
    var mapData = this._ensureMap(mapId);
    marker.isCustom = true;
    marker.id = 'custom-' + Date.now();
    mapData.customMarkers.push(marker);
    this.save();
    return marker;
  },

  updateCustomMarker: function(mapId, markerId, updates) {
    var mapData = this._ensureMap(mapId);
    var marker = mapData.customMarkers.find(function(m) { return m.id === markerId; });
    if (marker) {
      Object.keys(updates).forEach(function(key) { marker[key] = updates[key]; });
      this.save();
    }
    return marker;
  },

  deleteCustomMarker: function(mapId, markerId) {
    var mapData = this._ensureMap(mapId);
    mapData.customMarkers = mapData.customMarkers.filter(function(m) { return m.id !== markerId; });
    this.save();
  }
};

Progress.load();
</script>
```

- [ ] **Step 2: Update marker popup to include Mark Found button and Notes field**

In the main app script, replace the marker placement loop with:

```js
    // --- Track Leaflet markers for later updates ---
    var leafletMarkers = {};

    function createPopupContent(marker) {
      var isFound = Progress.isFound(currentMapId, marker.id);
      var note = Progress.getNote(currentMapId, marker.id);
      var catInfo = categoryMap[marker.categoryId];
      var catTitle = catInfo ? catInfo.category.title : '';

      var container = document.createElement('div');
      container.className = 'cdm-popup';

      var title = document.createElement('b');
      title.textContent = marker.title;
      container.appendChild(title);

      var catLabel = document.createElement('div');
      catLabel.style.cssText = 'font-size:11px;color:#aaa;margin:2px 0 4px;';
      catLabel.textContent = catTitle;
      container.appendChild(catLabel);

      if (marker.description) {
        var desc = document.createElement('div');
        desc.style.cssText = 'font-size:12px;margin-bottom:6px;';
        desc.textContent = marker.description;
        container.appendChild(desc);
      }

      var noteLabel = document.createElement('label');
      noteLabel.style.cssText = 'font-size:11px;color:#aaa;display:block;margin-top:4px;';
      noteLabel.textContent = 'Notes:';
      container.appendChild(noteLabel);

      var noteInput = document.createElement('textarea');
      noteInput.style.cssText = 'width:100%;height:40px;resize:vertical;font-size:12px;margin:2px 0 6px;background:#2a2a4a;color:#e0e0e0;border:1px solid #444;border-radius:3px;padding:4px;';
      noteInput.value = note;
      noteInput.addEventListener('blur', function() {
        Progress.setNote(currentMapId, marker.id, noteInput.value);
      });
      container.appendChild(noteInput);

      var btn = document.createElement('button');
      btn.style.cssText = 'width:100%;padding:6px;cursor:pointer;border:none;border-radius:4px;font-size:13px;font-weight:bold;' +
        (isFound ? 'background:#27ae60;color:#fff;' : 'background:#444;color:#ccc;');
      btn.textContent = isFound ? '✓ Found' : 'Mark as Found';
      btn.addEventListener('click', function() {
        var nowFound = Progress.toggleFound(currentMapId, marker.id);
        updateMarkerAppearance(marker.id, nowFound);
        // Refresh popup content
        var lm = leafletMarkers[marker.id];
        if (lm) {
          lm.setPopupContent(createPopupContent(marker));
        }
        updateProgressDisplay();
      });
      container.appendChild(btn);

      return container;
    }

    function updateMarkerAppearance(markerId, isFound) {
      var lm = leafletMarkers[markerId];
      if (!lm) return;
      var el = lm.getElement();
      if (el) {
        el.style.opacity = isFound ? '0.5' : '1';
        var inner = el.querySelector('.cdm-marker-inner');
        var check = el.querySelector('.cdm-check');
        if (isFound && !check) {
          var checkEl = document.createElement('div');
          checkEl.className = 'cdm-check';
          checkEl.style.cssText = 'position:absolute;top:-4px;right:-4px;background:#27ae60;color:#fff;width:14px;height:14px;border-radius:50%;font-size:10px;text-align:center;line-height:14px;';
          checkEl.textContent = '✓';
          el.querySelector('.cdm-marker') ? el.querySelector('.cdm-marker').appendChild(checkEl) : el.appendChild(checkEl);
        } else if (!isFound && check) {
          check.remove();
        }
      }
    }

    // --- Place markers ---
    currentMarkerData.markers.forEach(function(marker) {
      var latlng = L.latLng(marker.y, marker.x);
      var icon = createMarkerIcon(marker.categoryId);
      var lm = L.marker(latlng, { icon: icon }).addTo(map);
      lm.bindPopup(createPopupContent(marker), { maxWidth: 250 });
      leafletMarkers[marker.id] = lm;

      // Apply found state on load
      if (Progress.isFound(currentMapId, marker.id)) {
        lm.on('add', function() { updateMarkerAppearance(marker.id, true); });
        // Also try immediately
        setTimeout(function() { updateMarkerAppearance(marker.id, true); }, 0);
      }
    });
```

- [ ] **Step 3: Open in browser and verify**

Open `index.html` in browser. Click a marker — popup should show title, category, description, notes field, and "Mark as Found" button. Click "Mark as Found" — marker should dim to 50% opacity and show green checkmark. Refresh page — found state should persist.

- [ ] **Step 4: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add localStorage progress tracking with found toggle and notes in popups
EOF
)"
```

---

### Task 4: Sidebar with Category Groups, Toggles, and Progress

**Files:**
- Modify: `index.html` (add sidebar HTML, CSS, and JS)

- [ ] **Step 1: Add sidebar CSS**

Add these styles inside the existing `<style>` block:

```css
    #sidebar {
      position: absolute; top: 0; left: 0; bottom: 0; width: 280px; z-index: 1000;
      background: #1a1a2e; border-right: 1px solid #333; overflow-y: auto;
      display: flex; flex-direction: column;
    }
    #sidebar-header {
      padding: 12px; border-bottom: 1px solid #333; flex-shrink: 0;
    }
    #sidebar-header h2 { font-size: 16px; margin: 0 0 8px; color: #fff; }
    #search-input {
      width: 100%; padding: 6px 10px; background: #2a2a4a; border: 1px solid #444;
      border-radius: 4px; color: #e0e0e0; font-size: 13px; outline: none;
    }
    #search-input:focus { border-color: #c0392b; }
    #sidebar-categories { flex: 1; overflow-y: auto; padding: 4px 0; }
    .group-header {
      padding: 8px 12px; cursor: pointer; font-weight: bold; font-size: 13px;
      display: flex; align-items: center; gap: 6px; user-select: none;
    }
    .group-header:hover { background: rgba(255,255,255,0.05); }
    .group-arrow { font-size: 10px; transition: transform 0.15s; width: 12px; text-align: center; }
    .group-arrow.collapsed { transform: rotate(-90deg); }
    .group-categories { padding-left: 8px; }
    .group-categories.hidden { display: none; }
    .category-row {
      padding: 4px 12px; display: flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer;
    }
    .category-row:hover { background: rgba(255,255,255,0.05); }
    .category-checkbox { width: 14px; height: 14px; accent-color: #c0392b; cursor: pointer; }
    .category-icon {
      width: 18px; height: 18px; border-radius: 50%; text-align: center; line-height: 18px;
      font-size: 9px; font-weight: bold; color: #fff; flex-shrink: 0;
    }
    .category-title { flex: 1; }
    .category-count { color: #888; font-size: 11px; }
    #sidebar-footer {
      padding: 12px; border-top: 1px solid #333; flex-shrink: 0;
    }
    .progress-bar-container {
      background: #2a2a4a; border-radius: 4px; height: 16px; overflow: hidden; margin: 4px 0;
    }
    .progress-bar-fill {
      height: 100%; background: #27ae60; transition: width 0.3s; border-radius: 4px;
    }
    .progress-text { font-size: 12px; color: #aaa; text-align: center; }
    #map { left: 280px !important; }
    .leaflet-popup-content-wrapper { background: #1a1a2e; color: #e0e0e0; border: 1px solid #444; }
    .leaflet-popup-tip { background: #1a1a2e; border: 1px solid #444; }
    .leaflet-popup-close-button { color: #aaa !important; }
```

- [ ] **Step 2: Add sidebar HTML**

Add this HTML **before** the `<div id="map">`:

```html
  <div id="sidebar">
    <div id="sidebar-header">
      <h2>Crimson Desert Map</h2>
      <input type="text" id="search-input" placeholder="Search markers...">
    </div>
    <div id="sidebar-categories"></div>
    <div id="sidebar-footer">
      <div class="progress-text" id="progress-text">0/0 found</div>
      <div class="progress-bar-container">
        <div class="progress-bar-fill" id="progress-bar" style="width:0%"></div>
      </div>
    </div>
  </div>
```

- [ ] **Step 3: Add sidebar rendering JS**

Add this in the main app script, after the `categoryMap` construction and before marker placement:

```js
    // --- Category visibility state ---
    var categoryVisibility = {};
    currentMarkerData.groups.forEach(function(group) {
      group.categories.forEach(function(cat) {
        categoryVisibility[cat.id] = true;
      });
    });

    // --- Render Sidebar ---
    function renderSidebar() {
      var container = document.getElementById('sidebar-categories');
      container.innerHTML = '';

      currentMarkerData.groups.forEach(function(group) {
        // Group header
        var header = document.createElement('div');
        header.className = 'group-header';

        var arrow = document.createElement('span');
        arrow.className = 'group-arrow';
        arrow.textContent = '▼';

        var colorDot = document.createElement('span');
        colorDot.style.cssText = 'width:10px;height:10px;border-radius:50%;background:' + group.color + ';flex-shrink:0;';

        var titleSpan = document.createElement('span');
        titleSpan.textContent = group.title;

        header.appendChild(arrow);
        header.appendChild(colorDot);
        header.appendChild(titleSpan);
        container.appendChild(header);

        // Categories container
        var catsDiv = document.createElement('div');
        catsDiv.className = 'group-categories';

        group.categories.forEach(function(cat) {
          var row = document.createElement('div');
          row.className = 'category-row';

          var checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.className = 'category-checkbox';
          checkbox.checked = categoryVisibility[cat.id] !== false;
          checkbox.addEventListener('change', function() {
            categoryVisibility[cat.id] = checkbox.checked;
            applyFilters();
          });

          var iconSpan = document.createElement('span');
          iconSpan.className = 'category-icon';
          iconSpan.style.background = group.color;
          iconSpan.textContent = cat.icon;

          var titleSpan = document.createElement('span');
          titleSpan.className = 'category-title';
          titleSpan.textContent = cat.title;

          var counts = Progress.getFoundCount(currentMapId, cat.id, currentMarkerData.markers);
          var countSpan = document.createElement('span');
          countSpan.className = 'category-count';
          countSpan.id = 'count-' + cat.id;
          countSpan.textContent = counts.found + '/' + counts.total;

          row.appendChild(checkbox);
          row.appendChild(iconSpan);
          row.appendChild(titleSpan);
          row.appendChild(countSpan);
          catsDiv.appendChild(row);
        });

        container.appendChild(catsDiv);

        // Toggle collapse
        header.addEventListener('click', function() {
          var isHidden = catsDiv.classList.toggle('hidden');
          arrow.classList.toggle('collapsed', isHidden);
        });
      });
    }

    // --- Apply visibility filters ---
    function applyFilters() {
      var searchText = document.getElementById('search-input').value.toLowerCase();

      currentMarkerData.markers.forEach(function(marker) {
        var lm = leafletMarkers[marker.id];
        if (!lm) return;

        var catVisible = categoryVisibility[marker.categoryId] !== false;
        var matchesSearch = !searchText || marker.title.toLowerCase().indexOf(searchText) !== -1;
        var isFound = Progress.isFound(currentMapId, marker.id);

        if (!catVisible) {
          // Category hidden — hide marker entirely
          lm.getElement() && (lm.getElement().style.display = 'none');
        } else {
          lm.getElement() && (lm.getElement().style.display = '');
          if (!matchesSearch) {
            lm.getElement() && (lm.getElement().style.opacity = '0.2');
          } else if (isFound) {
            lm.getElement() && (lm.getElement().style.opacity = '0.5');
          } else {
            lm.getElement() && (lm.getElement().style.opacity = '1');
          }
        }
      });
    }

    // --- Update progress display ---
    function updateProgressDisplay() {
      var totals = Progress.getTotalCount(currentMapId, currentMarkerData.markers);
      var pct = totals.total > 0 ? Math.round((totals.found / totals.total) * 100) : 0;
      document.getElementById('progress-text').textContent = totals.found + '/' + totals.total + ' found (' + pct + '%)';
      document.getElementById('progress-bar').style.width = pct + '%';

      // Update per-category counts
      currentMarkerData.groups.forEach(function(group) {
        group.categories.forEach(function(cat) {
          var counts = Progress.getFoundCount(currentMapId, cat.id, currentMarkerData.markers);
          var el = document.getElementById('count-' + cat.id);
          if (el) el.textContent = counts.found + '/' + counts.total;
        });
      });
    }

    // --- Search ---
    document.getElementById('search-input').addEventListener('input', function() {
      applyFilters();
    });
```

- [ ] **Step 4: Call renderSidebar and updateProgressDisplay after markers are placed**

Add these calls at the end of the main app script:

```js
    renderSidebar();
    updateProgressDisplay();
```

- [ ] **Step 5: Open in browser and verify**

Expected: Sidebar on the left with search box, two collapsible groups (Locations, Collectibles), category checkboxes with progress counts, and overall progress bar at the bottom. Unchecking a category hides its markers. Marking items as found updates the counts. Searching dims non-matching markers.

- [ ] **Step 6: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add sidebar with category groups, toggles, search filter, and progress tracking
EOF
)"
```

---

### Task 5: Top Bar with Map Selector and Tools Menu

**Files:**
- Modify: `index.html` (add top bar, map switching, tools dropdown)

- [ ] **Step 1: Add top bar CSS**

Add to the `<style>` block:

```css
    #topbar {
      position: absolute; top: 0; left: 280px; right: 0; height: 44px; z-index: 1000;
      background: #1a1a2e; border-bottom: 1px solid #333; display: flex; align-items: center;
      padding: 0 12px; gap: 12px;
    }
    #topbar-title { font-size: 14px; font-weight: bold; color: #fff; white-space: nowrap; }
    #map-selector {
      padding: 4px 8px; background: #2a2a4a; border: 1px solid #444; border-radius: 4px;
      color: #e0e0e0; font-size: 13px; cursor: pointer;
    }
    .topbar-spacer { flex: 1; }
    .topbar-btn {
      padding: 4px 10px; background: #2a2a4a; border: 1px solid #444; border-radius: 4px;
      color: #e0e0e0; font-size: 13px; cursor: pointer; white-space: nowrap;
    }
    .topbar-btn:hover { background: #3a3a5a; }
    #tools-menu {
      position: absolute; top: 44px; right: 12px; background: #1a1a2e; border: 1px solid #444;
      border-radius: 4px; z-index: 1001; display: none; min-width: 180px;
    }
    #tools-menu.visible { display: block; }
    .tools-item {
      padding: 8px 14px; cursor: pointer; font-size: 13px; display: block; width: 100%;
      background: none; border: none; color: #e0e0e0; text-align: left;
    }
    .tools-item:hover { background: rgba(255,255,255,0.08); }
    .tools-separator { border-top: 1px solid #333; margin: 2px 0; }
    #map { top: 44px !important; }
```

- [ ] **Step 2: Add top bar HTML**

Add this HTML **before** the sidebar div:

```html
  <div id="topbar">
    <span id="topbar-title">Crimson Desert Map</span>
    <select id="map-selector"></select>
    <span class="topbar-spacer"></span>
    <button class="topbar-btn" id="btn-add-marker" title="Add custom marker">+ Add</button>
    <button class="topbar-btn" id="btn-tools" title="Tools">⚙</button>
    <div id="tools-menu">
      <button class="tools-item" id="tool-export">Export Progress</button>
      <button class="tools-item" id="tool-import">Import Progress</button>
      <div class="tools-separator"></div>
      <button class="tools-item" id="tool-export-markers">Export Marker Data</button>
      <div class="tools-separator"></div>
      <button class="tools-item" id="tool-import-save">Import Save (Future)</button>
      <div class="tools-separator"></div>
      <button class="tools-item" id="tool-reset" style="color:#e74c3c;">Reset Progress</button>
    </div>
  </div>
```

- [ ] **Step 3: Add top bar JS — map selector and tools toggle**

Add to the main app script:

```js
    // --- Populate map selector ---
    var mapSelector = document.getElementById('map-selector');
    window.CDM_MAPS.forEach(function(m) {
      var opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.title;
      if (m.id === currentMapId) opt.selected = true;
      mapSelector.appendChild(opt);
    });

    mapSelector.addEventListener('change', function() {
      var newMapId = mapSelector.value;
      var newConfig = window.CDM_MAPS.find(function(m) { return m.id === newMapId; });
      if (!newConfig) return;

      // Check if marker data is loaded
      if (!window.CDM_MARKERS[newMapId]) {
        // Dynamically load marker data
        var script = document.createElement('script');
        script.src = newConfig.markersFile;
        script.onload = function() { switchToMap(newMapId, newConfig); };
        script.onerror = function() { console.warn('Failed to load markers for', newMapId); };
        document.head.appendChild(script);
      } else {
        switchToMap(newMapId, newConfig);
      }
    });

    function switchToMap(newMapId, newConfig) {
      currentMapId = newMapId;
      currentMapConfig = newConfig;
      currentMarkerData = window.CDM_MARKERS[newMapId];

      // Rebuild category map
      categoryMap = {};
      categoryVisibility = {};
      currentMarkerData.groups.forEach(function(group) {
        group.categories.forEach(function(cat) {
          categoryMap[cat.id] = { category: cat, group: group };
          categoryVisibility[cat.id] = true;
        });
      });

      // Clear and rebuild map layers
      map.eachLayer(function(layer) { map.removeLayer(layer); });
      leafletMarkers = {};

      // Add new image overlay
      L.imageOverlay(newConfig.image, newConfig.bounds).addTo(map);
      map.fitBounds(newConfig.bounds);

      // Place markers
      currentMarkerData.markers.forEach(function(marker) {
        var latlng = L.latLng(marker.y, marker.x);
        var icon = createMarkerIcon(marker.categoryId);
        var lm = L.marker(latlng, { icon: icon }).addTo(map);
        lm.bindPopup(createPopupContent(marker), { maxWidth: 250 });
        leafletMarkers[marker.id] = lm;
        if (Progress.isFound(currentMapId, marker.id)) {
          setTimeout(function() { updateMarkerAppearance(marker.id, true); }, 0);
        }
      });

      // Also place custom markers
      placeCustomMarkers();

      document.getElementById('search-input').value = '';
      renderSidebar();
      updateProgressDisplay();
    }

    // --- Tools menu toggle ---
    document.getElementById('btn-tools').addEventListener('click', function(e) {
      e.stopPropagation();
      document.getElementById('tools-menu').classList.toggle('visible');
    });
    document.addEventListener('click', function() {
      document.getElementById('tools-menu').classList.remove('visible');
    });
```

- [ ] **Step 4: Open in browser and verify**

Expected: Top bar shows title, map selector dropdown (with "The Continent" selected), "+ Add" button, and "⚙" tools button. Clicking ⚙ shows dropdown menu. Map selector works if multiple maps exist.

- [ ] **Step 5: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add top bar with map selector and tools dropdown menu
EOF
)"
```

---

### Task 6: Import/Export Progress

**Files:**
- Modify: `index.html` (wire up export/import/reset tools)

- [ ] **Step 1: Add hidden file input for import**

Add this HTML right before the closing `</body>` tag:

```html
  <input type="file" id="import-file-input" accept=".json" style="display:none">
```

- [ ] **Step 2: Add export/import/reset JS**

Add to the main app script:

```js
    // --- Export Progress ---
    document.getElementById('tool-export').addEventListener('click', function() {
      var data = Progress.getData();
      var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      var date = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = 'crimson-desert-progress-' + date + '.json';
      a.click();
      URL.revokeObjectURL(url);
      document.getElementById('tools-menu').classList.remove('visible');
    });

    // --- Import Progress ---
    document.getElementById('tool-import').addEventListener('click', function() {
      document.getElementById('import-file-input').click();
      document.getElementById('tools-menu').classList.remove('visible');
    });

    document.getElementById('import-file-input').addEventListener('change', function(e) {
      var file = e.target.files[0];
      if (!file) return;

      var reader = new FileReader();
      reader.onload = function(evt) {
        try {
          var imported = JSON.parse(evt.target.result);
          if (typeof imported !== 'object' || imported === null) {
            alert('Invalid progress file format.');
            return;
          }

          var mode = confirm('Merge with existing progress?\n\nOK = Merge (keep existing + add new)\nCancel = Replace (overwrite everything)');

          if (mode) {
            // Merge
            var current = Progress.getData();
            Object.keys(imported).forEach(function(key) {
              if (key === 'schemaVersion') return;
              if (!current[key]) {
                current[key] = imported[key];
              } else {
                // Merge found arrays (union)
                if (imported[key].found) {
                  imported[key].found.forEach(function(id) {
                    if (current[key].found.indexOf(id) === -1) {
                      current[key].found.push(id);
                    }
                  });
                }
                // Merge notes (imported wins on conflict)
                if (imported[key].notes) {
                  Object.keys(imported[key].notes).forEach(function(nk) {
                    current[key].notes[nk] = imported[key].notes[nk];
                  });
                }
                // Merge custom markers (dedup by id)
                if (imported[key].customMarkers) {
                  var existingIds = {};
                  current[key].customMarkers.forEach(function(m) { existingIds[m.id] = true; });
                  imported[key].customMarkers.forEach(function(m) {
                    if (!existingIds[m.id]) {
                      current[key].customMarkers.push(m);
                    }
                  });
                }
              }
            });
            Progress.save();
          } else {
            // Replace
            Progress._data = imported;
            if (!Progress._data.schemaVersion) Progress._data.schemaVersion = 1;
            Progress.save();
          }

          // Refresh display
          switchToMap(currentMapId, currentMapConfig);
          alert('Progress imported successfully!');
        } catch (err) {
          alert('Failed to import: ' + err.message);
        }
      };
      reader.readAsText(file);
      // Reset file input so same file can be imported again
      e.target.value = '';
    });

    // --- Export Marker Data ---
    document.getElementById('tool-export-markers').addEventListener('click', function() {
      var data = currentMarkerData;
      var jsContent = 'window.CDM_MARKERS = window.CDM_MARKERS || {};\nwindow.CDM_MARKERS["' + currentMapId + '"] = ' + JSON.stringify(data, null, 2) + ';\n';
      var blob = new Blob([jsContent], { type: 'application/javascript' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = currentMapId + '.js';
      a.click();
      URL.revokeObjectURL(url);
      document.getElementById('tools-menu').classList.remove('visible');
    });

    // --- Import Save (future placeholder) ---
    document.getElementById('tool-import-save').addEventListener('click', function() {
      alert('Save file parsing is not yet available.\n\nWhen a parser is built, drop the parsed.json file here.');
      document.getElementById('tools-menu').classList.remove('visible');
    });

    // --- Reset Progress ---
    document.getElementById('tool-reset').addEventListener('click', function() {
      document.getElementById('tools-menu').classList.remove('visible');
      var choice = prompt('Reset progress?\n\nType "this" to reset current map only.\nType "all" to reset everything.\nPress Cancel to abort.');
      if (!choice) return;
      choice = choice.toLowerCase().trim();

      if (choice === 'this') {
        var data = Progress.getData();
        delete data[currentMapId];
        Progress.save();
        switchToMap(currentMapId, currentMapConfig);
        alert('Progress reset for ' + currentMapConfig.title);
      } else if (choice === 'all') {
        Progress._data = { schemaVersion: 1 };
        Progress.save();
        switchToMap(currentMapId, currentMapConfig);
        alert('All progress reset.');
      }
    });
```

- [ ] **Step 3: Open in browser and verify**

Test flow:
1. Mark a few items as found
2. Click ⚙ → Export Progress → saves a JSON file
3. Reset progress (type "this")
4. Import the exported file → progress restored
5. Verify merge vs replace works

- [ ] **Step 4: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add import/export progress, export marker data, and reset progress tools
EOF
)"
```

---

### Task 7: Custom Markers (Add, Edit, Delete, Drag)

**Files:**
- Modify: `index.html` (custom marker CRUD)

- [ ] **Step 1: Add custom marker CSS**

Add to the `<style>` block:

```css
    .cdm-custom-marker div {
      border-style: dashed !important;
      transform: rotate(45deg);
      border-radius: 4px !important;
    }
    #add-marker-banner {
      position: absolute; top: 50px; left: 50%; transform: translateX(-50%); z-index: 1001;
      background: #c0392b; color: #fff; padding: 8px 20px; border-radius: 4px; font-size: 13px;
      display: none; cursor: pointer;
    }
    #add-marker-banner.visible { display: block; }
```

- [ ] **Step 2: Add banner HTML**

Add after the topbar div:

```html
  <div id="add-marker-banner">Click on the map to place a marker. <u>Cancel</u></div>
```

- [ ] **Step 3: Add custom marker JS**

Add to the main app script:

```js
    // --- Custom Marker Mode ---
    var isAddingMarker = false;

    document.getElementById('btn-add-marker').addEventListener('click', function() {
      isAddingMarker = true;
      document.getElementById('add-marker-banner').classList.add('visible');
      document.getElementById('map').style.cursor = 'crosshair';
    });

    document.getElementById('add-marker-banner').addEventListener('click', function() {
      isAddingMarker = false;
      document.getElementById('add-marker-banner').classList.remove('visible');
      document.getElementById('map').style.cursor = '';
    });

    // Right-click also enters add mode and immediately places
    map.on('contextmenu', function(e) {
      showAddMarkerPopup(e.latlng);
    });

    map.on('click', function(e) {
      if (!isAddingMarker) return;
      isAddingMarker = false;
      document.getElementById('add-marker-banner').classList.remove('visible');
      document.getElementById('map').style.cursor = '';
      showAddMarkerPopup(e.latlng);
    });

    function showAddMarkerPopup(latlng) {
      var container = document.createElement('div');
      container.style.cssText = 'min-width:200px;';

      var heading = document.createElement('b');
      heading.textContent = 'Add Custom Marker';
      container.appendChild(heading);

      container.appendChild(document.createElement('br'));

      var titleLabel = document.createElement('label');
      titleLabel.textContent = 'Title:';
      titleLabel.style.cssText = 'font-size:11px;color:#aaa;display:block;margin-top:6px;';
      container.appendChild(titleLabel);

      var titleInput = document.createElement('input');
      titleInput.type = 'text';
      titleInput.style.cssText = 'width:100%;padding:4px;background:#2a2a4a;color:#e0e0e0;border:1px solid #444;border-radius:3px;font-size:12px;';
      container.appendChild(titleInput);

      var catLabel = document.createElement('label');
      catLabel.textContent = 'Category:';
      catLabel.style.cssText = 'font-size:11px;color:#aaa;display:block;margin-top:6px;';
      container.appendChild(catLabel);

      var catSelect = document.createElement('select');
      catSelect.style.cssText = 'width:100%;padding:4px;background:#2a2a4a;color:#e0e0e0;border:1px solid #444;border-radius:3px;font-size:12px;';

      // Add "Custom" option
      var customOpt = document.createElement('option');
      customOpt.value = 'custom';
      customOpt.textContent = 'Custom';
      catSelect.appendChild(customOpt);

      // Add existing categories
      currentMarkerData.groups.forEach(function(group) {
        group.categories.forEach(function(cat) {
          var opt = document.createElement('option');
          opt.value = cat.id;
          opt.textContent = group.title + ' > ' + cat.title;
          catSelect.appendChild(opt);
        });
      });
      container.appendChild(catSelect);

      var noteLabel = document.createElement('label');
      noteLabel.textContent = 'Note:';
      noteLabel.style.cssText = 'font-size:11px;color:#aaa;display:block;margin-top:6px;';
      container.appendChild(noteLabel);

      var noteInput = document.createElement('textarea');
      noteInput.style.cssText = 'width:100%;height:40px;resize:vertical;font-size:12px;background:#2a2a4a;color:#e0e0e0;border:1px solid #444;border-radius:3px;padding:4px;';
      container.appendChild(noteInput);

      var btnRow = document.createElement('div');
      btnRow.style.cssText = 'display:flex;gap:6px;margin-top:8px;';

      var addBtn = document.createElement('button');
      addBtn.textContent = 'Add';
      addBtn.style.cssText = 'flex:1;padding:6px;background:#27ae60;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:bold;';

      var cancelBtn = document.createElement('button');
      cancelBtn.textContent = 'Cancel';
      cancelBtn.style.cssText = 'flex:1;padding:6px;background:#444;color:#ccc;border:none;border-radius:4px;cursor:pointer;';

      btnRow.appendChild(addBtn);
      btnRow.appendChild(cancelBtn);
      container.appendChild(btnRow);

      var popup = L.popup({ maxWidth: 250, closeOnClick: false })
        .setLatLng(latlng)
        .setContent(container)
        .openOn(map);

      cancelBtn.addEventListener('click', function() { map.closePopup(popup); });

      addBtn.addEventListener('click', function() {
        var title = titleInput.value.trim();
        if (!title) { titleInput.style.borderColor = '#e74c3c'; return; }

        var markerData = {
          categoryId: catSelect.value,
          title: title,
          x: latlng.lng,
          y: latlng.lat,
          note: noteInput.value.trim()
        };

        var saved = Progress.addCustomMarker(currentMapId, markerData);
        map.closePopup(popup);
        placeOneCustomMarker(saved);
      });
    }

    function createCustomMarkerIcon(categoryId) {
      var info = categoryMap[categoryId];
      var color = info ? info.group.color : '#9b59b6';
      var label = info ? info.category.icon : '★';
      return L.divIcon({
        className: 'cdm-marker cdm-custom-marker',
        html: '<div style="background:' + color + ';width:22px;height:22px;border-radius:4px;text-align:center;line-height:22px;font-size:10px;font-weight:bold;color:#fff;border:2px dashed #fff;">' + label + '</div>',
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });
    }

    function placeOneCustomMarker(marker) {
      var latlng = L.latLng(marker.y, marker.x);
      var icon = createCustomMarkerIcon(marker.categoryId);
      var lm = L.marker(latlng, { icon: icon, draggable: true }).addTo(map);
      leafletMarkers[marker.id] = lm;

      lm.bindPopup(createCustomPopupContent(marker), { maxWidth: 250 });

      lm.on('dragend', function() {
        var pos = lm.getLatLng();
        Progress.updateCustomMarker(currentMapId, marker.id, { x: pos.lng, y: pos.lat });
      });
    }

    function createCustomPopupContent(marker) {
      var container = document.createElement('div');

      var title = document.createElement('b');
      title.textContent = marker.title;
      container.appendChild(title);

      var catInfo = categoryMap[marker.categoryId];
      var catLabel = document.createElement('div');
      catLabel.style.cssText = 'font-size:11px;color:#aaa;margin:2px 0 4px;';
      catLabel.textContent = (catInfo ? catInfo.category.title : 'Custom') + ' (custom)';
      container.appendChild(catLabel);

      if (marker.note) {
        var note = document.createElement('div');
        note.style.cssText = 'font-size:12px;margin-bottom:6px;';
        note.textContent = marker.note;
        container.appendChild(note);
      }

      var btnRow = document.createElement('div');
      btnRow.style.cssText = 'display:flex;gap:6px;margin-top:6px;';

      var deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.style.cssText = 'flex:1;padding:6px;background:#e74c3c;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:bold;font-size:12px;';
      deleteBtn.addEventListener('click', function() {
        Progress.deleteCustomMarker(currentMapId, marker.id);
        var lm = leafletMarkers[marker.id];
        if (lm) { map.removeLayer(lm); delete leafletMarkers[marker.id]; }
      });

      btnRow.appendChild(deleteBtn);
      container.appendChild(btnRow);

      return container;
    }

    function placeCustomMarkers() {
      var customs = Progress.getCustomMarkers(currentMapId);
      customs.forEach(function(marker) {
        placeOneCustomMarker(marker);
      });
    }

    // Place custom markers on initial load
    placeCustomMarkers();
```

- [ ] **Step 4: Open in browser and verify**

Test:
1. Click "+ Add" → banner appears → click map → popup to add custom marker
2. Fill in title, select category, add note → click Add → diamond-shaped marker appears
3. Drag custom marker to reposition
4. Click custom marker → popup with "Delete" button
5. Right-click empty space → same add popup
6. Refresh page → custom markers persist

- [ ] **Step 5: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add custom markers: create via toolbar/right-click, drag to move, delete
EOF
)"
```

---

### Task 8: Responsive Layout (Sidebar Toggle on Mobile)

**Files:**
- Modify: `index.html` (responsive CSS + hamburger toggle)

- [ ] **Step 1: Add responsive CSS**

Add to the `<style>` block:

```css
    #sidebar-toggle {
      display: none; position: absolute; top: 6px; left: 8px; z-index: 1002;
      background: #2a2a4a; border: 1px solid #444; border-radius: 4px; color: #e0e0e0;
      font-size: 18px; width: 32px; height: 32px; cursor: pointer; line-height: 30px; text-align: center;
    }
    @media (max-width: 768px) {
      #sidebar { transform: translateX(-100%); transition: transform 0.2s; }
      #sidebar.open { transform: translateX(0); }
      #sidebar-toggle { display: block; }
      #topbar { left: 0 !important; padding-left: 48px; }
      #map { left: 0 !important; }
    }
```

- [ ] **Step 2: Add hamburger toggle button HTML**

Add right after `<body>`:

```html
  <button id="sidebar-toggle">☰</button>
```

- [ ] **Step 3: Add toggle JS**

Add to the main app script:

```js
    // --- Sidebar toggle for mobile ---
    document.getElementById('sidebar-toggle').addEventListener('click', function() {
      document.getElementById('sidebar').classList.toggle('open');
    });

    // Close sidebar when clicking map on mobile
    map.on('click', function() {
      if (window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.remove('open');
      }
    });
```

- [ ] **Step 4: Verify at narrow width**

Resize browser to <768px width. Sidebar should be hidden. Hamburger (☰) button visible. Click it → sidebar slides in. Click map → sidebar closes.

- [ ] **Step 5: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add index.html
git commit -m "$(cat <<'EOF'
Add responsive layout: sidebar collapses to hamburger toggle on mobile
EOF
)"
```

---

### Task 9: Final Polish and Integration Test

**Files:**
- Modify: `index.html` (fix edge cases, final adjustments)

- [ ] **Step 1: Add .gitignore**

Create `.gitignore`:

```
saves/
*.swp
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Full integration test checklist**

Open `index.html` from file explorer (file:// protocol). Verify each item:

1. Map loads with placeholder image and 6 markers
2. Markers have colored circle icons with category initials
3. Click marker → popup with title, category, description, notes, "Mark as Found"
4. Mark found → marker dims, green checkmark appears
5. Sidebar shows groups with categories and checkboxes
6. Uncheck a category → its markers hide
7. Search → non-matching markers dim to 20%
8. Progress bar updates when marking items
9. Per-category counts update
10. "+ Add" → click map → add custom marker popup
11. Right-click → same add popup
12. Custom marker appears as diamond/dashed shape
13. Drag custom marker → position persists on reload
14. Delete custom marker via popup
15. ⚙ → Export Progress → downloads JSON
16. ⚙ → Reset Progress → type "this" → progress clears
17. ⚙ → Import Progress → load the exported file → progress restored
18. ⚙ → Export Marker Data → downloads .js file
19. Refresh page → all progress persists
20. Resize to mobile width → sidebar hides, hamburger appears
21. Map selector dropdown present (only one map for now)

- [ ] **Step 3: Commit**

```bash
cd C:/msys64/home/gelum/crimson_desert_map
git add .gitignore
git commit -m "$(cat <<'EOF'
Add .gitignore and complete integration testing
EOF
)"
```

---

## Summary

| Task | What it builds | Files |
|------|---------------|-------|
| 1 | Leaflet scaffold | `lib/*`, `index.html` |
| 2 | Map data + image overlay + markers | `data/*`, `index.html` |
| 3 | Progress tracking (found/notes) | `index.html` |
| 4 | Sidebar (groups, toggles, search, progress) | `index.html` |
| 5 | Top bar (map selector, tools) | `index.html` |
| 6 | Import/export/reset | `index.html` |
| 7 | Custom markers (CRUD + drag) | `index.html` |
| 8 | Responsive mobile layout | `index.html` |
| 9 | Integration test + gitignore | `.gitignore` |
