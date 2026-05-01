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
