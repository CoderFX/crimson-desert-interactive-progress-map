/**
 * Icon Map: MapGenie category icon names -> Metaforge PNG icon files
 *
 * Source: https://metaforge.app/crimson-desert/map/main
 * CDN:    https://cdn.metaforge.app/crimson-desert/map-icons/
 * Icons:  144 PNG files (white on transparent, ~200x200px)
 *
 * Usage:
 *   var file = METAFORGE_ICON_MAP[mapGenieIconName];
 *   if (file) { img.src = 'lib/icons/' + file; }
 *
 * Keys use underscores (MapGenie convention).
 * Values are the PNG filename in this directory.
 * null = no suitable metaforge icon found (fallback to font icon or generic).
 */
var METAFORGE_ICON_MAP = {
  // --- Locations ---
  "stronghold":            "strongholds.png",
  "abyss_cresset":         "abyss-cresset.png",
  "abyss_nexus":           "abyss-nexus.png",
  "bell":                  "bell.png",
  "cave":                  "cave.png",
  "greymane_shrine":       "shrine.png",
  "hidden_passage":        "hiddenspace.png",
  "point_of_interest":     "point-of-interest.png",
  "spire":                 "temple.png",
  "notice_board":          "notice-board.png",
  "secret_space":          "sanctum.png",
  "shadow_sanctum":        "sanctum.png",
  "well":                  null,               // no metaforge equivalent
  "witchs_hideout":        "witch-location.png",

  // --- Enemies ---
  "boss":                  "enemy.png",
  "elite_enemy":           "elite.png",
  "abyss_enemy":           "enemy.png",
  "mysterious_creature":   "cd_Icon_map_wyvern.png",
  "predator":              "animals.png",
  "walker":                "enemy.png",

  // --- Collectibles ---
  "treasure_chest":        "treasure-chest.png",
  "treasure_map":          "treasure-map.png",
  "treasure_map_solution": "treasure-map.png",
  "sealed_abyss_artifact": "sealed-abyss-artifact.png",
  "abyss_artifact":        "abyss-artifact.png",
  "abyss_gear":            "abyss-gears.png",
  "key_item":              "key-item.png",
  "memory_fragment":       "memory-fragment.png",
  "mount":                 "mount.png",
  "locked_treasure":       "treasure-chest.png",
  "constellation":         null,               // no metaforge equivalent

  // --- Items ---
  "weapon":                "weapon.png",
  "armor":                 "armor.png",
  "chest":                 "chest.png",
  "elixir":                "elixir.png",
  "accessory":             "accessory.png",
  "key":                   "key.png",
  "money":                 "money.png",
  "tool":                  "tool.png",
  "common_equipment":      "chest.png",
  "pack":                  "small-bag.png",
  "pet":                   "animals.png",

  // --- Recipes ---
  "recipe":                "recipe.png",
  "alchemy_recipe":        "recipe.png",
  "equipment_blueprint":   "recipe.png",
  "tool_blueprint":        "recipe.png",
  "dye":                   "dye-recipe.png",
  "kuku_pot_item":         "recipe.png",

  // --- Quests ---
  "main_quest":            "main-quest.png",
  "faction_quest":         "main-quest.png",
  "puzzle_clue":           "bounties.png",

  // --- Shop Services ---
  "equipment_shop":        "equipment-shop.png",
  "provisioners_shop":     "provisioners-shop.png",
  "grocers_shop":          "grocers-shop.png",
  "fishing_shop":          "fishing-shop.png",
  "furniture_shop":        "furniture-shop.png",
  "mineral_shop":          "mineral-shop.png",
  "pet_shop":              "pet-shop.png",
  "artwork_shop":          "artwork-shop.png",
  "back_alley_shop":       "back-alley-shop.png",
  "bank":                  "bank.png",
  "black_market_trading":  "black-market-trading-post.png",
  "butchery":              "butchery.png",
  "confessional":          "confessional.png",
  "contribution_shop":     "contribution-shop.png",
  "dyehouse":              "dyehouse.png",
  "guard_station":         "guard-station.png",
  "horse_black_market":    "horse-black-market.png",
  "inn":                   "inn.png",
  "livestock_fence":       "livestock-fence.png",
  "research_institute":    "research-institute.png",
  "royal_trading_post":    "royal-trading-post.png",
  "saddlery":              "saddlery.png",
  "secret_shop":           "secret-shop.png",
  "smithy":                "smithy.png",
  "stable":                "stable.png",
  "street_shop":           "street-shop.png",
  "tailors_shop":          "tailors-shop.png",
  "tannery":               "tannery.png",
  "wagon_fence":           "wagon-fence.png",
  "kuku_shop":             "kilden-kuku-workshop.png",
  "decorative_stone_shop": "statue-shop.png",
  "ranchers_shop":         "livestock-shop.png",
  "infirmary":             "drug-store.png",
  "barracks":              "strongholds.png",
  "timber_warehouse":      "warehouse.png",

  // --- Crafting Tools ---
  "anvil":                 "anvil.png",
  "bonfire":               "bonfire.png",
  "cauldron":              "cauldron.png",
  "grindstone":            "grindstone.png",

  // --- Resources - Ores & Minerals ---
  "iron_ore":              "iron-ore.png",
  "copper_ore":            "copper-ore.png",
  "gold_ore":              "gold-ore.png",
  "silver_ore":            "silver-ore.png",
  "bismuth_ore":           "bismuth-ore.png",
  "scolecite_ore":         "salt.png",
  "azurite":               "azurite.png",
  "epidote":               "epidote.png",
  "diamond":               "diamond.png",
  "garnet":                "ruby.png",
  "bloodstone":            "garnet.png",
  "brimstone":             "sulfur-stone.png",
  "mercury":               "pickaxe.png",
  "stone":                 "pickaxe.png",

  // --- Resources - Plants & Herbs ---
  "herb":                  "plants.png",
  "green_algae":           "plants.png",
  "red_seaweed":           "plants.png",
  "pine_mushroom":         "plants.png",
  "oakwood_mushroom":      "plants.png",
  "coral_mushroom":        "plants.png",
  "palmar_leaf":           "plants.png",
  "honey":                 "plants.png",
  "ginseng":               "plants.png",
  "spider_web":            "plants.png",
  "rubber":                "wood.png",
  "skyroot":               "wood.png",
  "produce":               "plants.png",

  // --- Animals ---
  "legendary_animal":      "animals.png",
  "prey_animal":           "animals.png",

  // --- NPCs & Skills ---
  "npc":                   "point-of-interest.png",
  "learn_skill":           null,               // no metaforge equivalent
  "reading_material":      "book-shop.png",

  // --- Minigames ---
  "minigame":              "duel.png",

  // --- Other ---
  "miscellaneous":         "point-of-interest.png",
  "easter_egg":            null,               // no metaforge equivalent
  "area":                  "ruins.png",
  "artillery_unit":        "cannon.png"
};

// --- Metaforge full category data (for reference/future use) ---
// Maps metaforge subcategory keys to their icon files and parent groups.
var METAFORGE_CATEGORIES = {
  // Group: Locations
  "abyss-cresset":          { icon: "abyss-cresset.png",          group: "locations" },
  "abyss-gate":             { icon: "abyss-gate.png",             group: "locations" },
  "abyss-nexus":            { icon: "abyss-nexus.png",            group: "locations" },
  "airship-station":        { icon: "airship-station.png",         group: "locations" },
  "bell":                   { icon: "bell.png",                    group: "locations" },
  "camp":                   { icon: "camp.png",                    group: "locations" },
  "camp-housing":           { icon: "camp-housing.png",            group: "locations" },
  "castle":                 { icon: "village.png",                 group: "locations" },
  "cave":                   { icon: "cave.png",                    group: "locations" },
  "carriage":               { icon: "carriage.png",                group: "locations" },
  "cemetery":               { icon: "cemetery.png",                group: "locations" },
  "dock":                   { icon: "anchor.png",                  group: "locations" },
  "fort":                   { icon: "strongholds.png",             group: "locations" },
  "fortress":               { icon: "strongholds.png",             group: "locations" },
  "hidden":                 { icon: "hiddenspace.png",             group: "locations" },
  "hidden-passage":         { icon: "hiddenspace.png",             group: "locations" },
  "lighthouse":             { icon: "lighthouse.png",              group: "locations" },
  "mine":                   { icon: "cave.png",                    group: "locations" },
  "monastery":              { icon: "monastery.png",               group: "locations" },
  "notice-board":           { icon: "notice-board.png",            group: "locations" },
  "outpost":                { icon: "tower.png",                   group: "locations" },
  "point-of-interest":      { icon: "point-of-interest.png",       group: "locations" },
  "port":                   { icon: "anchor.png",                  group: "locations" },
  "prison":                 { icon: "prison.png",                  group: "locations" },
  "quarry":                 { icon: "cave.png",                    group: "locations" },
  "ruins":                  { icon: "ruins.png",                   group: "locations" },
  "sanctum":                { icon: "sanctum.png",                 group: "locations" },
  "sawmill":                { icon: "shed.png",                    group: "locations" },
  "shrine":                 { icon: "shrine.png",                  group: "locations" },
  "spire":                  { icon: "temple.png",                  group: "locations" },
  "skybridge-gate":         { icon: "skybridge-gate.png",          group: "locations" },
  "stronghold":             { icon: "strongholds.png",             group: "locations" },
  "temple":                 { icon: "temple.png",                  group: "locations" },
  "town-city":              { icon: "town-city.png",               group: "locations" },
  "trade-post":             { icon: "strongholds.png",             group: "locations" },
  "village":                { icon: "village.png",                  group: "locations" },
  "watchtower":             { icon: "tower.png",                   group: "locations" },
  "witch-location":         { icon: "witch-location.png",          group: "locations" },
  "workshop":               { icon: "shed.png",                    group: "locations" },

  // Group: Shop Services
  "alchemy-shop":           { icon: "alchemy-shop.png",            group: "shop-services" },
  "artwork-shop":           { icon: "artwork-shop.png",            group: "shop-services" },
  "auction-house":          { icon: "auction-house.png",           group: "shop-services" },
  "back-alley-shop":        { icon: "back-alley-shop.png",         group: "shop-services" },
  "bank":                   { icon: "bank.png",                    group: "shop-services" },
  "book-shop":              { icon: "book-shop.png",               group: "shop-services" },
  "barbershop":             { icon: "barbershop.png",              group: "shop-services" },
  "black-market-trading-post": { icon: "black-market-trading-post.png", group: "shop-services" },
  "butchery":               { icon: "butchery.png",                group: "shop-services" },
  "carriage-workshop":      { icon: "carriage-workshop.png",       group: "shop-services" },
  "cannon-shop":            { icon: "cannon-shop.png",             group: "shop-services" },
  "confessional":           { icon: "confessional.png",            group: "shop-services" },
  "contribution-shop":      { icon: "contribution-shop.png",       group: "shop-services" },
  "donation-box":           { icon: "donation-box.png",            group: "shop-services" },
  "drug-store":             { icon: "drug-store.png",              group: "shop-services" },
  "dyehouse":               { icon: "dyehouse.png",               group: "shop-services" },
  "equipment-shop":         { icon: "equipment-shop.png",          group: "shop-services" },
  "fishing-shop":           { icon: "fishing-shop.png",            group: "shop-services" },
  "furniture-shop":         { icon: "furniture-shop.png",          group: "shop-services" },
  "grocers-shop":           { icon: "grocers-shop.png",            group: "shop-services" },
  "guard-station":          { icon: "guard-station.png",           group: "shop-services" },
  "horse-black-market":     { icon: "horse-black-market.png",      group: "shop-services" },
  "saddlery":               { icon: "saddlery.png",                group: "shop-services" },
  "inn":                    { icon: "inn.png",                     group: "shop-services" },
  "jewelry-shop":           { icon: "jewelry-shop.png",            group: "shop-services" },
  "kilden-kuku-workshop":   { icon: "kilden-kuku-workshop.png",    group: "shop-services" },
  "livestock-fence":        { icon: "livestock-fence.png",         group: "shop-services" },
  "livestock-shop":         { icon: "livestock-shop.png",          group: "shop-services" },
  "mineral-shop":           { icon: "mineral-shop.png",            group: "shop-services" },
  "pet-shop":               { icon: "pet-shop.png",               group: "shop-services" },
  "provisioners-shop":      { icon: "provisioners-shop.png",       group: "shop-services" },
  "research-institute":     { icon: "research-institute.png",      group: "shop-services" },
  "royal-trading-post":     { icon: "royal-trading-post.png",      group: "shop-services" },
  "seed-shop":              { icon: "seed-shop.png",               group: "shop-services" },
  "secret-shop":            { icon: "secret-shop.png",             group: "shop-services" },
  "smithy":                 { icon: "smithy.png",                  group: "shop-services" },
  "stable":                 { icon: "stable.png",                  group: "shop-services" },
  "statue-shop":            { icon: "statue-shop.png",             group: "shop-services" },
  "street-shop":            { icon: "street-shop.png",             group: "shop-services" },
  "tailors-shop":           { icon: "tailors-shop.png",            group: "shop-services" },
  "tannery":                { icon: "tannery.png",                 group: "shop-services" },
  "trade-storage":          { icon: "trade-storage.png",           group: "shop-services" },
  "wagon-fence":            { icon: "wagon-fence.png",             group: "shop-services" },
  "wandering-merchant":     { icon: "wandering-merchant.png",      group: "shop-services" },
  "warehouse":              { icon: "warehouse.png",               group: "shop-services" },
  "witch-shop":             { icon: "witch-shop.png",              group: "shop-services" },

  // Group: Crafting Tools
  "anvil":                  { icon: "anvil.png",                   group: "crafting-tools" },
  "bonfire":                { icon: "bonfire.png",                 group: "crafting-tools" },
  "cauldron":               { icon: "cauldron.png",                group: "crafting-tools" },
  "cook":                   { icon: "special-cooking-tool.png",    group: "crafting-tools" },
  "grindstone":             { icon: "grindstone.png",              group: "crafting-tools" },
  "special-cooking-tool":   { icon: "special-cooking-tool.png",    group: "crafting-tools" },

  // Group: Collectibles
  "abyss-artifact":         { icon: "abyss-artifact.png",          group: "collectibles" },
  "key-item":               { icon: "key-item.png",               group: "collectibles" },
  "memory-fragment":        { icon: "memory-fragment.png",         group: "collectibles" },
  "mount":                  { icon: "mount.png",                   group: "collectibles" },
  "sealed-abyss-artifact":  { icon: "sealed-abyss-artifact.png",  group: "collectibles" },
  "treasure-chest":         { icon: "treasure-chest.png",          group: "collectibles" },
  "treasure-map":           { icon: "treasure-map.png",            group: "collectibles" },
  "treasure-map-solution":  { icon: "treasure-map.png",            group: "collectibles" },

  // Group: Quests
  "bounties":               { icon: "bounties.png",                group: "quests" },
  "faction-quest":          { icon: "main-quest.png",              group: "quests" },
  "main-quest":             { icon: "main-quest.png",              group: "quests" },

  // Group: Recipes
  "provisions":             { icon: "recipe.png",                  group: "recipes" },
  "equipment-blueprint":    { icon: "recipe.png",                  group: "recipes" },
  "abyss-gears":            { icon: "abyss-gears.png",            group: "recipes" },
  "dye-recipe":             { icon: "dye-recipe.png",              group: "recipes" },
  "kuku-pot":               { icon: "recipe.png",                  group: "recipes" },
  "alchemy-recipe":         { icon: "recipe.png",                  group: "recipes" },
  "tool-recipe":            { icon: "recipe.png",                  group: "recipes" },

  // Group: Minigames
  "arm-wrestling":          { icon: "arm-wrestling.png",           group: "minigames" },
  "archery-contest":        { icon: "archery-contest.png",         group: "minigames" },
  "card-game":              { icon: "card-game.png",               group: "minigames" },
  "ceelo":                  { icon: "ceelo.png",                   group: "minigames" },
  "duel":                   { icon: "duel.png",                    group: "minigames" },
  "unarmed-duel":           { icon: "unarmed-duel.png",            group: "minigames" },
  "gambling":               { icon: "gambling.png",                group: "minigames" },
  "horse-race":             { icon: "horse-race.png",              group: "minigames" },
  "hand-wrestling":         { icon: "hand-wrestling.png",          group: "minigames" },
  "spear-contest":          { icon: "spear-contest.png",           group: "minigames" },
  "rock-paper-scissors":    { icon: "rock-paper-scissors.png",     group: "minigames" },
  "seotda":                 { icon: "seotda.png",                  group: "minigames" },
  "shooting-contest":       { icon: "shooting-contest.png",        group: "minigames" },
  "swordsmanship-contest":  { icon: "swordsmanship-contest.png",   group: "minigames" },
  "slapping-contest":       { icon: "slapping-contest.png",        group: "minigames" },
  "wrestling":              { icon: "hand-wrestling.png",          group: "minigames" },

  // Group: Items
  "accessory":              { icon: "accessory.png",               group: "items" },
  "armor":                  { icon: "armor.png",                   group: "items" },
  "chest":                  { icon: "chest.png",                   group: "items" },
  "elixir":                 { icon: "elixir.png",                  group: "items" },
  "key":                    { icon: "key.png",                     group: "items" },
  "money":                  { icon: "money.png",                   group: "items" },
  "palmar-pill":            { icon: "palmar-pill.png",             group: "items" },
  "refined-palmar-pill":    { icon: "refined-palmar-pill.png",     group: "items" },
  "small-bag":              { icon: "small-bag.png",               group: "items" },
  "tool":                   { icon: "tool.png",                    group: "items" },
  "weapon":                 { icon: "weapon.png",                  group: "items" },

  // Group: Enemies
  "story-boss":             { icon: "enemy.png",                   group: "enemies" },
  "world-boss":             { icon: "world-boss.png",              group: "enemies" },
  "elite":                  { icon: "elite.png",                   group: "enemies" },
  "mysterious-creature":    { icon: "cd_Icon_map_wyvern.png",      group: "enemies" },
  "creature":               { icon: "cd_Icon_map_wyvern.png",      group: "enemies" },

  // Group: Other
  "fishing-spot":           { icon: "fishing-spot.png",            group: "other" },
  "fixed-crossbow":         { icon: "fixed-crossbow.png",          group: "other" },
  "cannon":                 { icon: "cannon.png",                  group: "other" },
  "ballista":               { icon: "ballista.png",                group: "other" },
  "miscellaneous":          { icon: "point-of-interest.png",       group: "other" },
  "singijeon":              { icon: "singijeon.png",               group: "other" }
};
