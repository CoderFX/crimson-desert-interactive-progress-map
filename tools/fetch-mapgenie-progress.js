/**
 * MapGenie Progress Fetcher
 *
 * Converts your MapGenie found locations into a progress file
 * compatible with the Crimson Desert Interactive Progress Map.
 *
 * USAGE:
 *   1. Go to https://mapgenie.io/crimson-desert/maps/pywel (logged in)
 *   2. Open DevTools (F12) > Console
 *   3. Paste this ENTIRE script and press Enter
 *   4. A progress JSON file will download automatically
 *   5. Use "Import Progress" in the map app to load it
 */

(function() {
  // Check if we're on MapGenie
  if (!window.store || !window.store.getState) {
    alert('This script must be run on a MapGenie map page.\n\nGo to: https://mapgenie.io/crimson-desert/maps/pywel');
    return;
  }

  var state = window.store.getState();
  var foundLocations = state.user ? state.user.foundLocations : null;

  if (!foundLocations || Object.keys(foundLocations).length === 0) {
    alert('No found locations detected.\n\nMake sure you are logged in to MapGenie and have marked some locations as found.');
    return;
  }

  // Convert MapGenie IDs to our format
  var foundIds = Object.keys(foundLocations).map(function(id) {
    return 'loc-' + id;
  });

  // Build progress object
  var progress = {
    schemaVersion: 1,
    pywel: {
      found: foundIds,
      notes: {},
      customMarkers: []
    }
  };

  // Download as JSON file
  var blob = new Blob([JSON.stringify(progress, null, 2)], { type: 'application/json' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  var date = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = 'mapgenie-progress-' + date + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  console.log('Exported ' + foundIds.length + ' found locations to mapgenie-progress-' + date + '.json');
  console.log('Use "Import Progress" in the Crimson Desert Interactive Map to load this file.');
})();
