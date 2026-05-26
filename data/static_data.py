# Ability Score Generation — Option C (Hybrid Auto-Assign):
# The bot rolls 4d6-drop-lowest for 6 values, sorts them highest to lowest,
# then maps them to stats based on class priority. This guarantees every class
# gets their best roll in their primary stat (e.g. Wizard always gets highest in INT,
# Fighter in STR) while keeping the randomness of rolling. Players can reroll once
# but cannot manually reassign — the class determines stat placement.
CLASS_STAT_PRIORITY = {
    "Barbarian": ["Strength","Constitution","Dexterity","Wisdom","Charisma","Intelligence"],
    "Bard":      ["Charisma","Dexterity","Constitution","Wisdom","Intelligence","Strength"],
    "Cleric":    ["Wisdom","Constitution","Strength","Charisma","Dexterity","Intelligence"],
    "Druid":     ["Wisdom","Constitution","Dexterity","Intelligence","Charisma","Strength"],
    "Warrior":   ["Strength","Constitution","Dexterity","Wisdom","Charisma","Intelligence"],
    "Monk":      ["Dexterity","Wisdom","Constitution","Strength","Charisma","Intelligence"],
    "Necromancer":["Intelligence","Constitution","Wisdom","Dexterity","Charisma","Strength"],
    "Paladin":   ["Strength","Charisma","Constitution","Wisdom","Dexterity","Intelligence"],
    "Ranger":    ["Dexterity","Wisdom","Constitution","Strength","Intelligence","Charisma"],
    "Rogue":     ["Dexterity","Constitution","Wisdom","Charisma","Intelligence","Strength"],
    "Deathknight":["Strength","Constitution","Charisma","Wisdom","Dexterity","Intelligence"],
    "Sorcerer":  ["Charisma","Constitution","Dexterity","Wisdom","Intelligence","Strength"],
    "Warlock":   ["Charisma","Constitution","Dexterity","Wisdom","Intelligence","Strength"],
    "Wizard":    ["Intelligence","Constitution","Dexterity","Wisdom","Charisma","Strength"],
}

RACES = ["Human","Elf","Dwarf","Halfling","Dragonborn","Gnome","Half-Elf","Half-Orc","Tiefling"]

# Class title progression — titles change as players level up, shown on character sheet.
# Format: class -> [(min_level, title), ...] ordered ascending. Last match wins.
CLASS_TITLES = {
    "Barbarian":   [(1,"Barbarian"), (5,"Berserker"), (10,"Warchief"), (15,"Ravager"), (20,"Primal Lord")],
    "Bard":        [(1,"Bard"), (5,"Minstrel"), (10,"Troubadour"), (15,"Virtuoso"), (20,"Maestro")],
    "Cleric":      [(1,"Cleric"), (5,"Vicar"), (10,"Templar"), (15,"High Priest"), (20,"Archon")],
    "Druid":       [(1,"Druid"), (5,"Wanderer"), (10,"Preserver"), (15,"Hierophant"), (20,"Storm Warden")],
    "Warrior":     [(1,"Warrior"), (5,"Champion"), (10,"Myrmidon"), (15,"Warlord"), (20,"Overlord")],
    "Monk":        [(1,"Monk"), (5,"Disciple"), (10,"Master"), (15,"Grandmaster"), (20,"Transcendent")],
    "Necromancer": [(1,"Necromancer"), (5,"Heretic"), (10,"Defiler"), (15,"Deathspeaker"), (20,"Arch Lich")],
    "Paladin":     [(1,"Paladin"), (5,"Cavalier"), (10,"Knight"), (15,"Crusader"), (20,"Seraphim")],
    "Ranger":      [(1,"Ranger"), (5,"Pathfinder"), (10,"Outrider"), (15,"Warden"), (20,"Forest Stalker")],
    "Rogue":       [(1,"Rogue"), (5,"Rake"), (10,"Blackguard"), (15,"Assassin"), (20,"Deceiver")],
    "Deathknight":[(1,"Deathknight"), (5,"Reaver"), (10,"Revenant"), (15,"Grave Lord"), (20,"Doomknight")],
    "Sorcerer":    [(1,"Sorcerer"), (5,"Channeler"), (10,"Evoker"), (15,"Arch Mage"), (20,"Arcanist")],
    "Warlock":     [(1,"Warlock"), (5,"Hexblade"), (10,"Beguiler"), (15,"Phantasmist"), (20,"Coercer")],
    "Wizard":      [(1,"Wizard"), (5,"Evoker"), (10,"Conjurer"), (15,"Arch Mage"), (20,"Arch Convoker")],
}

def get_class_title(char_class, level):
    """Return the appropriate title for a class at a given level."""
    titles = CLASS_TITLES.get(char_class, [(1, char_class)])
    title = char_class
    for min_lvl, t in titles:
        if level >= min_lvl:
            title = t
    return title
CLASSES = ["Barbarian","Bard","Cleric","Druid","Monk","Necromancer","Paladin","Ranger","Rogue","Deathknight","Sorcerer","Warlock","Warrior","Wizard"]
BACKGROUNDS = ["Acolyte","Criminal","Folk Hero","Noble","Outlander","Sage","Soldier","Charlatan","Entertainer","Hermit"]
ABILITY_SCORES = ["Strength","Dexterity","Constitution","Intelligence","Wisdom","Charisma"]

SUBCLASSES = {
    "Barbarian": ["Berserker","Totem Warden"],
    "Bard": ["Songweaver","Warbard"],
    "Cleric": ["Holy","Discipline","Shadow"],
    "Druid": ["Restoration","Feral","Balance"],
    "Warrior": ["Arms","Fury","Protection"],
    "Monk": ["Windwalker","Shadowstep","Elementalist"],
    "Necromancer": ["Reanimator","Harvester","Lichborn"],
    "Paladin": ["Protection","Holy","Retribution"],
    "Ranger": ["Marksmanship","Beast Mastery","Survival"],
    "Rogue": ["Subtlety","Assassination","Outlaw"],
    "Deathknight": ["Blood","Unholy","Frost"],
    "Sorcerer": ["Arcane","Frost","Fire"],
    "Warlock": ["Demonology","Affliction","Destruction"],
    "Wizard": ["Divination","Enchantment","Conjuration"],
}

CLASS_HP = {
    "Barbarian":12,"Warrior":10,"Paladin":10,"Ranger":10,"Deathknight":10,
    "Bard":8,"Cleric":8,"Druid":8,"Monk":8,"Rogue":8,"Warlock":8,
    "Necromancer":6,"Sorcerer":6,"Wizard":6
}

# Starting equipment per class: (weapon_to_equip, armor_key_for_setac, shield, inventory_items)
# Weapons are intentionally the WEAKEST option each class is proficient with,
# leaving room for upgrades via loot during the campaign.
CLASS_STARTING_EQUIPMENT = {
    "Barbarian": ("handaxe",        "no armor",      False, ["handaxe","handaxe","explorer's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Bard":      ("dagger",         "chain mail",    True,  ["dagger","lute","diplomat's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Cleric":    ("mace",           "chain mail",    True,  ["mace","chain mail","shield","holy symbol","priest's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Druid":     ("dagger",         "leather",       True,  ["dagger","wooden shield","druidic focus","explorer's pack","health potion","health potion","health potion","resurrection scroll","Antidote Vial"]),
    "Warrior":   ("handaxe",        "chain mail",    True,  ["handaxe","chain mail","shield","explorer's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Monk":      ("dagger",         "no armor",      False, ["dagger","10 darts","explorer's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Necromancer":("dagger",        "no armor",      False, ["dagger","arcane focus","scholar's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Paladin":   ("mace",           "chain mail",    True,  ["mace","chain mail","shield","holy symbol","priest's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Ranger":    ("dagger",         "chain mail",    False, ["dagger","chain mail","quiver","20 arrows","explorer's pack","health potion","health potion","health potion","resurrection scroll","Antidote Vial"]),
    "Rogue":     ("dagger",         "leather",       False, ["dagger","thieves' tools","burglar's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Deathknight":("handaxe",      "chain mail",    True,  ["handaxe","chain mail","shield","unholy symbol","explorer's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Sorcerer":  ("quarterstaff",   "no armor",      False, ["quarterstaff","arcane focus","explorer's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Warlock":   ("dagger",         "leather",       False, ["dagger","arcane focus","scholar's pack","health potion","health potion","health potion","resurrection scroll"]),
    "Wizard":    ("quarterstaff",   "no armor",      False, ["quarterstaff","spellbook","arcane focus","scholar's pack","health potion","health potion","health potion","resurrection scroll"]),
}

# Spell slots per class per level [lvl1..lvl9] indexed by character level 1-20
CLASS_SLOT_TABLE = {
    "Bard": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
    "Cleric": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
    "Druid": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
    "Paladin": {
        1:[0,0,0,0,0,0,0,0,0], 2:[2,0,0,0,0,0,0,0,0], 3:[3,0,0,0,0,0,0,0,0],
        4:[3,0,0,0,0,0,0,0,0], 5:[4,2,0,0,0,0,0,0,0], 6:[4,2,0,0,0,0,0,0,0],
        7:[4,3,0,0,0,0,0,0,0], 8:[4,3,0,0,0,0,0,0,0], 9:[4,3,2,0,0,0,0,0,0],
        10:[4,3,2,0,0,0,0,0,0],11:[4,3,3,0,0,0,0,0,0],12:[4,3,3,0,0,0,0,0,0],
        13:[4,3,3,1,0,0,0,0,0],14:[4,3,3,1,0,0,0,0,0],15:[4,3,3,2,0,0,0,0,0],
        16:[4,3,3,2,0,0,0,0,0],17:[4,3,3,3,1,0,0,0,0],18:[4,3,3,3,1,0,0,0,0],
        19:[4,3,3,3,2,0,0,0,0],20:[4,3,3,3,2,0,0,0,0],
    },
    "Deathknight": {
        1:[0,0,0,0,0,0,0,0,0], 2:[2,0,0,0,0,0,0,0,0], 3:[3,0,0,0,0,0,0,0,0],
        4:[3,0,0,0,0,0,0,0,0], 5:[4,2,0,0,0,0,0,0,0], 6:[4,2,0,0,0,0,0,0,0],
        7:[4,3,0,0,0,0,0,0,0], 8:[4,3,0,0,0,0,0,0,0], 9:[4,3,2,0,0,0,0,0,0],
        10:[4,3,2,0,0,0,0,0,0],11:[4,3,3,0,0,0,0,0,0],12:[4,3,3,0,0,0,0,0,0],
        13:[4,3,3,1,0,0,0,0,0],14:[4,3,3,1,0,0,0,0,0],15:[4,3,3,2,0,0,0,0,0],
        16:[4,3,3,2,0,0,0,0,0],17:[4,3,3,3,1,0,0,0,0],18:[4,3,3,3,1,0,0,0,0],
        19:[4,3,3,3,2,0,0,0,0],20:[4,3,3,3,2,0,0,0,0],
    },
    "Ranger": {
        1:[0,0,0,0,0,0,0,0,0], 2:[2,0,0,0,0,0,0,0,0], 3:[3,0,0,0,0,0,0,0,0],
        4:[3,0,0,0,0,0,0,0,0], 5:[4,2,0,0,0,0,0,0,0], 6:[4,2,0,0,0,0,0,0,0],
        7:[4,3,0,0,0,0,0,0,0], 8:[4,3,0,0,0,0,0,0,0], 9:[4,3,2,0,0,0,0,0,0],
        10:[4,3,2,0,0,0,0,0,0],11:[4,3,3,0,0,0,0,0,0],12:[4,3,3,0,0,0,0,0,0],
        13:[4,3,3,1,0,0,0,0,0],14:[4,3,3,1,0,0,0,0,0],15:[4,3,3,2,0,0,0,0,0],
        16:[4,3,3,2,0,0,0,0,0],17:[4,3,3,3,1,0,0,0,0],18:[4,3,3,3,1,0,0,0,0],
        19:[4,3,3,3,2,0,0,0,0],20:[4,3,3,3,2,0,0,0,0],
    },
    "Sorcerer": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
    "Warlock": {
        1:[1,0,0,0,0,0,0,0,0], 2:[2,0,0,0,0,0,0,0,0], 3:[0,2,0,0,0,0,0,0,0],
        4:[0,2,0,0,0,0,0,0,0], 5:[0,0,2,0,0,0,0,0,0], 6:[0,0,2,0,0,0,0,0,0],
        7:[0,0,0,2,0,0,0,0,0], 8:[0,0,0,2,0,0,0,0,0], 9:[0,0,0,0,2,0,0,0,0],
        10:[0,0,0,0,2,0,0,0,0],11:[0,0,0,0,3,0,0,0,0],12:[0,0,0,0,3,0,0,0,0],
        13:[0,0,0,0,3,0,0,0,0],14:[0,0,0,0,3,0,0,0,0],15:[0,0,0,0,3,0,0,0,0],
        16:[0,0,0,0,3,0,0,0,0],17:[0,0,0,0,4,0,0,0,0],18:[0,0,0,0,4,0,0,0,0],
        19:[0,0,0,0,4,0,0,0,0],20:[0,0,0,0,4,0,0,0,0],
    },
    "Wizard": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
    "Necromancer": {
        1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
        4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
        7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
        13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
        16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
        19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
    },
}

XP_THRESHOLDS = {1:0,2:300,3:900,4:2700,5:6500,6:14000,7:23000,8:34000,9:48000,10:64000,
                 11:85000,12:100000,13:120000,14:140000,15:165000,16:195000,17:225000,18:265000,19:305000,20:355000}

ARMOR_TABLE = {
    "no armor":       10, "padded":11, "leather":11, "studded leather":12,
    "hide":12, "chain shirt":13, "scale mail":14, "breastplate":14,
    "half plate":15, "ring mail":14, "chain mail":16, "splint":17, "plate":18,
    "shield": 2,  # bonus, not base
}

# Armor categories for proficiency enforcement
LIGHT_ARMOR = {"padded", "leather", "studded leather"}
MEDIUM_ARMOR = {"hide", "chain shirt", "scale mail", "breastplate", "half plate"}
HEAVY_ARMOR = {"ring mail", "chain mail", "splint", "plate"}

# Class armor proficiencies: class -> set of allowed categories
CLASS_ARMOR_PROF = {
    "Barbarian":   {"light", "medium", "shield"},
    "Bard":        {"light", "medium", "heavy", "shield"},
    "Cleric":      {"light", "medium", "heavy", "shield"},
    "Druid":       {"light", "medium", "shield"},
    "Warrior":     {"light", "medium", "heavy", "shield"},
    "Monk":        {"light"},
    "Necromancer": {"light"},
    "Paladin":     {"light", "medium", "heavy", "shield"},
    "Ranger":      {"light", "medium", "heavy", "shield"},
    "Rogue":       {"light"},
    "Deathknight":{"light", "medium", "heavy", "shield"},
    "Sorcerer":    {"light"},
    "Warlock":     {"light"},
    "Wizard":      {"light"},
}

def get_armor_category(armor_key):
    """Return the category of an armor piece."""
    if armor_key in LIGHT_ARMOR: return "light"
    if armor_key in MEDIUM_ARMOR: return "medium"
    if armor_key in HEAVY_ARMOR: return "heavy"
    if armor_key == "shield": return "shield"
    return None

# ── Hostile Menagerie (Campaign Enemy Presets) ─────────────────────────────────

HOSTILE_MENAGERIE = {
    "furniture": {
        "name": "Animated Armor",
        "hp": 33, "ac": 18, "la": 0, "lr": 0, "xp": 200, "tier": 1, "min_level": 1,
        "attacks": "Slam +4, 1d6+2 bludgeoning",
        "traits": "Immune: poison, psychic. Condition immune: blinded, charmed, deafened, exhaustion, frightened, paralyzed, petrified, poisoned.",
        "loot": ["Splinterfang Hatchet", "5 gold"],
    },
    "rug": {
        "name": "Rug of Smothering",
        "hp": 33, "ac": 12, "la": 0, "lr": 0, "xp": 200, "tier": 1, "min_level": 1,
        "attacks": "Smother +5, 2d6+3 bludgeoning (grapple DC 13, blinded+restrained)",
        "traits": "Immune: poison, psychic. False Appearance (indistinguishable from normal rug).",
        "loot": [],
    },
    "shadow": {
        "name": "Shadow",
        "hp": 16, "ac": 12, "la": 0, "lr": 0, "xp": 100, "tier": 1, "min_level": 1,
        "attacks": "Strength Drain +4, 2d6+2 necrotic (target STR -1d4; dies if STR 0)",
        "traits": "Vulnerable: radiant. Resistant: acid, cold, fire, lightning, thunder, nonmagical physical. Immune: necrotic, poison. Amorphous. Shadow Stealth.",
        "loot": [],
    },
    "geometry": {
        "name": "The Geometry",
        "hp": 67, "ac": 9, "la": 0, "lr": 0, "xp": 450, "tier": 3, "min_level": 3,
        "attacks": "Fold +2, reach 10 ft, 5d6 bludgeoning. Unfold (Recharge 5-6): 15-ft radius, DEX DC 13, 3d6 force + pushed 10 ft.",
        "traits": "Aberrant Ground: 10-ft difficult terrain. Maddening Form: WIS DC 12 or 1d6 psychic + no reactions. At half HP: screams — all WIS DC 13 or +1 Dread.",
        "loot": ["Angle's Edge", "Fractal Wand", "Geometrist's Hide", "Folded Chain Shirt", "Vial of Spatial Mending"],
    },
    "echo": {
        "name": "The Echo",
        "hp": 52, "ac": 14, "la": 0, "lr": 0, "xp": 700, "tier": 3, "min_level": 3,
        "attacks": "Multiattack: 2x Slam +6, 1d6+4. Mirror Strike (Recharge 5-6): copies last attack, redirects at random ally.",
        "traits": "Shapechanger: reads thoughts — first attack each round has disadvantage. 'I Know You' (1/round): speaks fear, WIS DC 14 or frightened.",
        "loot": ["Mirrorbane Rapier", "Copycat Shortbow", "Echo Staff", "Echoweave Leather", "Reflective Chain", "Tincture of Clarity", "10 gold"],
    },
    "memory": {
        "name": "The Memory",
        "hp": 100, "ac": 15, "la": 3, "lr": 0, "xp": 2900, "tier": 4, "min_level": 4,
        "attacks": "Multiattack: 2x Void Strike +7, reach 10 ft, 2d8+4 force (WIS DC 15 or +1 Dread). Consume (Recharge 5-6): 20-ft cone, DEX DC 15, 4d8 necrotic + restrained.",
        "traits": "Immune: poison, psychic, necrotic. Resist: nonmagical physical. Legendary Actions (3): Shift (room rotates, DEX DC 12 or prone), Darkness (halve light), Whisper (2 actions, WIS DC 15 or frightened + 2d6 psychic). Phase 2 at half HP: +2 AC, 4 LA/round, sphere expands.",
        "loot": ["Voidcleaver Greatsword", "Hollowshot Longbow", "Soulcrusher Maul", "Mindbreak Staff", "Voidweave Robes", "Voidtouched Breastplate", "Abyssal Plate", "Essence of Forgotten Breath", "50 gold"],
    },
    "memory_p2": {
        "name": "The Memory (Phase 2)",
        "hp": 50, "ac": 17, "la": 4, "lr": 0, "xp": 0, "tier": 4, "min_level": 4,
        "attacks": "Same as Phase 1. Sphere hazard: ending turn within 5 ft = 2d8 force + STR DC 14 or pulled inside.",
        "traits": "All Phase 1 traits. Sphere expanding. Lair: gravity reverse (DEX DC 13, 2d6 fall), void wall (WIS DC 13 or walk toward it), sphere pulse (1d8 force in 15 ft).",
        "loot": ["Hungering Blade", "Tome of Unmaking", "Hollowhide Leather", "Hollowplate", "Heart of the House", "75 gold"],
    },
    "remnant": {
        "name": "House Remnant",
        "hp": 76, "ac": 15, "la": 0, "lr": 0, "xp": 450, "tier": 1, "min_level": 1,
        "attacks": "Multiattack: 2x Slam +7, 2d8+4 bludgeoning. Engulf: both slams hit = grapple (DC 14), restrained, 2d8+4 at start of turn.",
        "traits": "Immune: lightning. The corridor collapses: back 10 ft destroyed each round (4d6 bludgeoning + pushed forward).",
        "loot": ["Longsword of the Remnant", "Dust of Mending"],
    },
    "angle": {
        "name": "Minor Angle",
        "hp": 10, "ac": 12, "la": 0, "lr": 0, "xp": 50, "tier": 1, "min_level": 1,
        "attacks": "Slash +4, 1d6+2 force",
        "traits": "Shadow creature. Harasses backline. Flees from radiant.",
        "loot": [],
    },
    "mimic": {
        "name": "Mimic",
        "hp": 58, "ac": 12, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Pseudopod +5, 1d8+3 bludgeoning. Bite +5, 1d8+3 piercing + grapple (escape DC 13).",
        "traits": "Shapechanger: indistinguishable from a chest until it attacks. Adhesive: creature that touches it is grappled. Immune to acid. Surprise round if players open it without checking.",
        "loot": ["health potion", "health potion", "25 gold"],
    },
    # ── Tier 1: Fodder ─────────────────────────────────────────────────────────
    "crawling claw": {
        "name": "Crawling Claw",
        "hp": 2, "ac": 12, "la": 0, "lr": 0, "xp": 10, "tier": 1, "min_level": 1,
        "attacks": "Claw +3, 1d4+1 bludgeoning",
        "traits": "Immune: poison. Condition immune: charmed, exhaustion, poisoned. Blindsight 30 ft.",
        "loot": [],
    },
    "specter": {
        "name": "Specter",
        "hp": 22, "ac": 12, "la": 0, "lr": 0, "xp": 200, "tier": 1, "min_level": 1,
        "attacks": "Life Drain +4, 3d6 necrotic (CON DC 10 or max HP reduced by damage taken)",
        "traits": "Resistant: acid, cold, fire, lightning, thunder, nonmagical physical. Immune: necrotic, poison. Incorporeal Movement. Sunlight Sensitivity.",
        "loot": [],
    },
    # ── Tier 2: Mid-threat ─────────────────────────────────────────────────────
    "gibbering mouther": {
        "name": "Gibbering Mouther",
        "hp": 67, "ac": 9, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 3,
        "attacks": "Multiattack: Bite +2, 5d6 piercing (hits random target in 5 ft). Blinding Spittle (Recharge 5-6): 15 ft, DEX DC 13 or blinded 1 turn.",
        "traits": "Aberrant Ground: 10-ft radius difficult terrain, DEX DC 10 or fall prone. Gibbering: creatures within 20 ft, WIS DC 10 or confused (random direction).",
        "loot": [],
        "spawn_gif": "vfx/entity_vfx/gibbering_mouther.gif",
    },
    "poltergeist": {
        "name": "Poltergeist",
        "hp": 22, "ac": 12, "la": 0, "lr": 0, "xp": 200, "tier": 2, "min_level": 2,
        "attacks": "Forceful Slam +4, 3d6 force. Telekinetic Thrust: STR DC 12 or pushed 10 ft + prone.",
        "traits": "Invisible. Incorporeal Movement. Resistant: acid, cold, fire, lightning, thunder, nonmagical physical. Immune: necrotic, poison.",
        "loot": [],
    },
    "will-o-wisp": {
        "name": "Will-o'-Wisp",
        "hp": 22, "ac": 19, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 3,
        "attacks": "Shock +4, 2d8 lightning",
        "traits": "Immune: lightning, poison. Resistant: acid, cold, fire, necrotic, thunder, nonmagical physical. Incorporeal. Ephemeral (can't wear/carry). Consume Life: bonus action, invisible creature within 5 ft at 0 HP dies, wisp regains 3d6 HP.",
        "loot": [],
    },
    "nothic": {
        "name": "Nothic",
        "hp": 45, "ac": 15, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 3,
        "attacks": "Multiattack: 2x Claw +4, 1d6+3 slashing. Rotting Gaze (1/turn): 30 ft, CON DC 12, 3d6 necrotic.",
        "traits": "Truesight 120 ft. Weird Insight: contests Deception vs its Insight +5, learns one secret on success.",
        "loot": ["10 gold"],
    },
    "intellect devourer": {
        "name": "Intellect Devourer",
        "hp": 21, "ac": 12, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 3,
        "attacks": "Claws +4, 2d6+2 psychic. Devour Intellect: INT DC 12, 2d10 psychic — if INT reduced to 0, stunned until long rest.",
        "traits": "Blindsight 60 ft. Detect Sentience: senses creatures with INT 3+ within 300 ft. Body Thief: if target at 0 INT, takes over body.",
        "loot": [],
    },
    # ── Tier 3: Boss-adjacent ──────────────────────────────────────────────────
    "beholder": {
        "name": "Beholder",
        "hp": 180, "ac": 18, "la": 3, "lr": 3, "xp": 10000, "tier": 4, "min_level": 10,
        "attacks": "Bite +5, 4d6 piercing. Eye Rays (3/turn, random): 1=Charm Ray WIS DC 16, 2=Paralyzing Ray CON DC 16, 3=Fear Ray WIS DC 16, 4=Slowing Ray DEX DC 16, 5=Enervation Ray CON DC 16 8d8 necrotic, 6=Telekinetic Ray STR DC 16 pushed 30ft, 7=Sleep Ray WIS DC 16, 8=Petrification Ray DEX DC 16, 9=Disintegration Ray DEX DC 16 10d8 force, 10=Death Ray DEX DC 16 10d10 necrotic.",
        "traits": "Antimagic Cone: 150-ft cone, no magic functions inside. Legendary Actions (3): Eye Ray. Hover. Darkvision 120 ft.",
        "loot": ["Beholder Eye Stalk", "100 gold"],
        "spawn_gif": "vfx/entity_vfx/beholder.gif",
    },
    "beholder zombie": {
        "name": "Beholder Zombie",
        "hp": 93, "ac": 15, "la": 0, "lr": 0, "xp": 1800, "tier": 3, "min_level": 5,
        "attacks": "Bite +3, 4d6 piercing. Eye Ray (1d4 random): 1=Paralyzing Ray CON DC 14, 2=Fear Ray WIS DC 14, 3=Enervation Ray CON DC 14 2d8 necrotic, 4=Disintegration Ray DEX DC 14 4d8 force.",
        "traits": "Undead Fortitude: CON save DC 5+dmg to drop to 1 HP instead of 0 (not radiant/crit). Darkvision 60 ft.",
        "loot": ["Voidstone Shard", "50 gold"],
    },
    "wraith": {
        "name": "Wraith",
        "hp": 67, "ac": 13, "la": 0, "lr": 0, "xp": 1800, "tier": 3, "min_level": 5,
        "attacks": "Life Drain +6, 4d8+3 necrotic (CON DC 14 or max HP reduced). Create Specter: humanoid killed rises as specter under wraith's control.",
        "traits": "Resistant: acid, cold, fire, lightning, thunder, nonmagical physical. Immune: necrotic, poison. Incorporeal. Sunlight Sensitivity.",
        "loot": ["Wraithbone Ring"],
    },
    "banshee": {
        "name": "Banshee",
        "hp": 58, "ac": 12, "la": 0, "lr": 0, "xp": 1100, "tier": 3, "min_level": 4,
        "attacks": "Corrupting Touch +4, 3d6+2 necrotic. Wail (1/day): 30 ft, CON DC 13 or drop to 0 HP.",
        "traits": "Resistant: acid, cold, fire, lightning, thunder, nonmagical physical. Immune: necrotic, poison. Incorporeal. Detect Life 5 miles. Horrifying Visage: WIS DC 13 or frightened 1 min.",
        "loot": [],
    },
    "flameskull": {
        "name": "Flameskull",
        "hp": 40, "ac": 13, "la": 0, "lr": 0, "xp": 1100, "tier": 3, "min_level": 4,
        "attacks": "Fire Ray +5, 3d6 fire. Spellcasting: Fireball (8d6 fire, DEX DC 13), Magic Missile (3d4+3 force), Shield (reaction +5 AC).",
        "traits": "Immune: fire, poison. Illumination 15 ft. Rejuvenation: reforms in 1 hour unless holy water on remains. Magic Resistance.",
        "loot": ["Aldric's Research Notes"],
    },
    "invisible stalker": {
        "name": "Invisible Stalker",
        "hp": 104, "ac": 14, "la": 0, "lr": 0, "xp": 1800, "tier": 3, "min_level": 5,
        "attacks": "Multiattack: 2x Slam +6, 2d6+3 bludgeoning",
        "traits": "Invisible. Faultless Tracker: knows direction and distance to target. Resistant: nonmagical physical. Immune: poison. Condition immune: exhaustion, grappled, paralyzed, petrified, poisoned, prone, restrained, stunned.",
        "loot": [],
    },
    # ── Tier 4: Nightmare fuel ─────────────────────────────────────────────────
    "the lonely": {
        "name": "The Lonely",
        "hp": 112, "ac": 16, "la": 0, "lr": 0, "xp": 2900, "tier": 4, "min_level": 6,
        "attacks": "Multiattack: 2x Harpoon Arm +7, 2d10+4 piercing + pulled 10 ft. If both hit same target: grappled.",
        "traits": "Sorrowsworn. Psychic Leech: while grappling, target takes 3d6 psychic at start of its turn. Thrives on Isolation: advantage on attacks vs creatures with no allies within 5 ft.",
        "loot": ["Sorrow Fragment"],
    },
    "oblex": {
        "name": "Oblex",
        "hp": 75, "ac": 14, "la": 0, "lr": 0, "xp": 2900, "tier": 4, "min_level": 6,
        "attacks": "Pseudopod +7, 2d6+4 bludgeoning + 2d6 psychic. Eat Memories: INT DC 14, 2d6 psychic + stunned 1 turn on fail.",
        "traits": "Ooze. Sulfurous Impersonation: creates perfect copies of absorbed creatures (connected by slime tether). Amorphous. Aversion to Fire.",
        "loot": [],
    },
    "bodak": {
        "name": "Bodak",
        "hp": 58, "ac": 15, "la": 0, "lr": 0, "xp": 2300, "tier": 4, "min_level": 7,
        "attacks": "Fist +5, 1d4+3 bludgeoning + 2d8 necrotic. Withering Gaze: 30 ft, CON DC 13, 3d10 necrotic (half on save). Death Gaze (Recharge 6): CON DC 13 or drop to 0 HP.",
        "traits": "Immune: necrotic, poison. Resistant: cold, fire, nonmagical physical. Sunlight Hypersensitivity: 5 radiant per turn in sunlight. Aura of Annihilation: creatures starting turn within 30 ft take 5 necrotic.",
        "loot": [],
    },
    "star spawn mangler": {
        "name": "Star Spawn Mangler",
        "hp": 71, "ac": 14, "la": 0, "lr": 0, "xp": 1800, "tier": 4, "min_level": 5,
        "attacks": "Multiattack: 6x Claw +7, 1d8+4 slashing. Flurry of Claws: if 3+ hit same target, +2d8 psychic.",
        "traits": "Ambush: advantage on initiative. Shadow Stealth. Surprise attack: +2d6 damage on first hit if target is surprised.",
        "loot": [],
    },
    "boneclaw": {
        "name": "Boneclaw",
        "hp": 127, "ac": 16, "la": 0, "lr": 0, "xp": 5000, "tier": 4, "min_level": 8,
        "attacks": "Multiattack: 2x Piercing Claw +8, reach 15 ft, 3d10+4 piercing + grappled (escape DC 14). Shadow Jump (bonus): teleport 40 ft between shadows.",
        "traits": "Rejuvenation: reforms near master in 1d10 hours unless master dies. Shadow Stealth. Deadly Reach: opportunity attacks at 15 ft.",
        "loot": ["Boneclaw Talon"],
    },
    # ── Custom: House of Leaves Specials ───────────────────────────────────────
    "the grasp": {
        "name": "The Grasp",
        "hp": 45, "ac": 13, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 3,
        "attacks": "Void Pull +5, 2d8+3 necrotic (WIS DC 13 or pulled 10 ft; if pulled to 0 ft, restrained until end of target's next turn)",
        "traits": "Immune: poison, necrotic. Resistant: nonmagical physical. Incorporeal. The hands of everyone the house has consumed.",
        "loot": [],
        "spawn_gif": "vfx/entity_vfx/grasp.gif",
    },
    "the hallway": {
        "name": "The Hallway",
        "hp": 80, "ac": 8, "la": 1, "lr": 0, "xp": 1100, "tier": 3, "min_level": 3,
        "attacks": "Compress +6, 3d8 bludgeoning (all creatures, DEX DC 14 half). Extend: initiative count 20, hallway grows 30 ft — party must dash or be separated.",
        "traits": "The corridor IS the creature. Immune: poison, psychic, nonmagical physical. Vulnerable: force. Legendary Action (1): Shift — one player must WIS DC 13 or lose their sense of direction.",
        "loot": [],
    },
    "reflection": {
        "name": "Reflection",
        "hp": 0, "ac": 0, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Copies target player's weapon and stats exactly. Uses their attack bonus and damage.",
        "traits": "Mirror Entity: HP/AC/attacks = copied player. Always targets its original. Dies if original looks away (WIS DC 14 to avert gaze). Immune: psychic.",
        "loot": [],
    },
    "the furniture": {
        "name": "The Furniture",
        "hp": 55, "ac": 14, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Multiattack: Chair Slam +5 1d8+3, Table Sweep +5 2d6+3 (DEX DC 13 or prone), Lamp Hurl +5 1d6+3 fire.",
        "traits": "All objects in the room animate as one creature. Immune: poison, psychic. Vulnerable: fire. When reduced to half HP, splits into 2 smaller swarms (half stats each).",
        "loot": ["5 gold", "health potion"],
    },
    "threshold guardian": {
        "name": "Threshold Guardian",
        "hp": 45, "ac": 17, "la": 0, "lr": 0, "xp": 700, "tier": 2, "min_level": 3,
        "attacks": "Slam +6, 2d8+3 force. Riddle: asks a question about the player's fears/dreams. Correct = passage. Wrong = 3d6 psychic + Dread +1.",
        "traits": "A door that won't open. Immune: all damage until riddle is answered wrong. After wrong answer, becomes attackable for 3 rounds then resets.",
        "loot": [],
    },
    "bilge keeper": {
        "name": "Bilge Keeper",
        "hp": 76, "ac": 15, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Harpoon +5, 2d6+3 piercing (30% restrained on hit, CON DC 13)",
        "traits": "Immune: prone (sea legs). Waterlogged undead Viking. Carries keys to the grate.",
        "loot": ["Harpoon of the Deep", "Tidecaller Axe", "Barnacle Mail", "Drowned Leather", "health potion", "10 gold"],
    },
    "the cook": {
        "name": "The Cook",
        "hp": 45, "ac": 15, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Multiattack: 2x Claw +4, 1d6+3 slashing. Rotting Gaze (1/turn): 30 ft, CON DC 12, 3d6 necrotic.",
        "traits": "One enormous eye. Knows secrets (Weird Insight). Poison claws.",
        "loot": ["Coral Blade", "Drowned Leather", "Kelpweave Robes", "health potion", "15 gold"],
    },
    "drowned captain": {
        "name": "The Drowned Captain",
        "hp": 75, "ac": 16, "la": 2, "lr": 0, "xp": 1800, "tier": 3, "min_level": 3,
        "attacks": "Multiattack: 2x Coral Blade +7, 2d8+4 slashing + 1d6 cold. Undertow (Recharge 5-6): 15-ft cone, STR DC 15, 2d8 cold + prone + pulled 10 ft.",
        "traits": "Immune: cold, poison, frightened, prone. Resistant: nonmagical physical. Legendary Actions (2/round): Wave Slam, Pressure.",
        "loot": ["Coral Blade", "Stormbreaker Maul", "Coral Plate", "Kelpweave Robes", "50 gold"],
    },
    "depth horror": {
        "name": "Depth Horror",
        "hp": 95, "ac": 14, "la": 1, "lr": 0, "xp": 2300, "tier": 3, "min_level": 3, "regen": 10,
        "attacks": "Multiattack: 3x Tentacle Slam +7, 2d8+4 bludgeoning + grapple (escape DC 15). Abyssal Scream (Recharge 6): 30 ft, WIS DC 15, 4d8 psychic + frightened.",
        "traits": "The creature beneath the hull given form. Immune: cold, psychic. Resistant: nonmagical physical. Regeneration 10 HP/turn (stops in sunlight).",
        "loot": ["Krakens Tooth", "Sigrids Resolve", "Coral Plate", "Drowned Leather", "50 gold"],
    },
    "slappy": {
        "name": "Slappy",
        "hp": 60, "ac": 13, "regen": 1, "la": 0, "lr": 0, "xp": 500, "tier": 2, "min_level": 1,
        "attacks": "Bonk +5, 2d6+3 bludgeoning. Zap +5, 1d8+3 lightning.",
        "traits": "Test creature. Not part of any campaign. Immune: psychic.",
        "loot": ["Sword of Testing", "Shield of Debugging", "Potion of QA", "Helmet of Feedback", "10 gold"],
        "spawn_gif": "vfx/entity_vfx/slappy.gif",
    },
    "the measure": {
        "name": "The Measure",
        "hp": 38, "ac": 13, "la": 0, "lr": 0, "xp": 450, "tier": 2, "min_level": 2,
        "attacks": "Tape Lash +5, reach 15 ft, 2d6+3 slashing. Quantify: bonus action, target must INT DC 12 or be restrained by measuring tape for 1 turn.",
        "traits": "Obsessed with the 7-inch discrepancy. Attacks anyone who measures, counts, or says a number aloud. Immune: psychic. Vulnerable: fire.",
        "loot": ["Aldric's Measuring Tape"],
    },
}

# Common loot table — rolled for non-boss enemies with empty loot fields.
# One roll per active player when the enemy dies.
COMMON_LOOT_TABLE = [
    (1, 4, "5 gold"),
    (5, 7, "10 gold"),
    (8, 10, "health potion"),
    (11, 12, "Everlight Torch"),
    (13, 13, "Bandage"),
    (14, 16, "Antidote Vial"),
    (17, 18, "Smoke Bomb"),
    (19, 19, "Whetstone"),
    (20, 20, "Tincture of Clarity"),
    (21, 21, "Soul Fragment"),
]

async def roll_common_loot(channel):
    """Roll common loot table once per active player. Auto-distributes to each player's inventory."""
    chars = load_active_characters()
    if not chars:
        return
    player_count = get_active_player_count()
    # Use only the first N characters matching active player count
    recipients = chars[:player_count]
    lines = []
    for c in recipients:
        roll = random.randint(1, 21)
        item = None
        for low, high, loot_item in COMMON_LOOT_TABLE:
            if low <= roll <= high:
                item = loot_item
                break
        if not item:
            continue
        # Add to inventory
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        items.append(item)
        set_char_field(c["discord_id"], "inventory", ", ".join(items))
        # If it's gold, also add to gold field
        if item == "5 gold":
            set_char_field(c["discord_id"], "gold", (c.get("gold") or 0) + 5)
        elif item == "10 gold":
            set_char_field(c["discord_id"], "gold", (c.get("gold") or 0) + 10)
        lines.append(f"• **{c['char_name']}** received: {item}")
    if lines:
        embed = discord.Embed(title="💎 Loot Distributed!", color=discord.Color.gold())
        embed.description = "\n".join(lines)
        embed.set_footer(text="Items added to inventory. Use !trade to swap with allies.")
        await channel.send(embed=embed)

SIMPLE_WEAPONS = {"dagger","handaxe","mace","quarterstaff","spear"}
MARTIAL_WEAPONS = {"shortsword","longsword","greatsword","greataxe","rapier",
                   "shortbow","longbow","crossbow, light","warhammer","flail","morningstar"}
# Campaign loot weapons inherit proficiency from their base type
CAMPAIGN_WEAPONS = {
    "splinterfang hatchet": "handaxe",       # simple
    "angle's edge": "shortsword",            # martial
    "mirrorbane rapier": "rapier",           # martial
    "longsword of the remnant": "longsword", # martial
    "voidcleaver greatsword": "greatsword",  # martial
    "hollowshot longbow": "longbow",         # martial
    "aldric's paradox": "dagger",            # simple — anyone can use it
    "soulcrusher maul": "warhammer",         # martial
    "tidecaller axe": "handaxe",
    "coral blade": "longsword",
    "harpoon of the deep": "spear",
    "stormbreaker maul": "warhammer",
    "krakens tooth": "dagger",
    "sigrids resolve": "longsword",
    "sword of testing": "longsword",
}
ALL_WEAPONS = SIMPLE_WEAPONS | MARTIAL_WEAPONS | set(CAMPAIGN_WEAPONS.keys())

WEAPONS = {
    "unarmed":        ("1 bludgeoning", "—"),
    "dagger":         ("1d4 piercing",  "Finesse, light, thrown (20/60 ft)"),
    "shortsword":     ("1d6 piercing",  "Finesse, light"),
    "longsword":      ("1d8 slashing",  "Versatile (1d10)"),
    "greatsword":     ("2d6 slashing",  "Heavy, two-handed"),
    "handaxe":        ("1d6 slashing",  "Light, thrown (20/60 ft)"),
    "greataxe":       ("1d12 slashing", "Heavy, two-handed"),
    "rapier":         ("1d8 piercing",  "Finesse"),
    "shortbow":       ("1d6 piercing",  "Ammunition, range 80/320 ft, two-handed"),
    "longbow":        ("1d8 piercing",  "Ammunition, heavy, range 150/600 ft, two-handed"),
    "crossbow, light":("1d8 piercing",  "Ammunition, range 80/320 ft, loading, two-handed"),
    "quarterstaff":   ("1d6 bludgeoning","Versatile (1d8)"),
    "mace":           ("1d6 bludgeoning","—"),
    "warhammer":      ("1d8 bludgeoning","Versatile (1d10)"),
    "flail":          ("1d8 bludgeoning","—"),
    "morningstar":    ("1d8 piercing",  "—"),
    "spear":          ("1d6 piercing",  "Thrown (20/60 ft), versatile (1d8)"),
    # ── Campaign Loot Weapons (The House That Hungers) ─────────────────────────
    "splinterfang hatchet":    ("1d6+1 slashing", "Light, thrown (20/60 ft). Carved from animated wood — hums faintly."),
    "angle's edge":            ("1d6+1 piercing", "Finesse, light. Blade bends at impossible angles — ignores half cover."),
    "mirrorbane rapier":       ("1d8+1 piercing", "Finesse. Reflects no light. +1 to hit vs shapechangers."),
    "longsword of the remnant":("1d8+1 slashing", "Versatile (1d10+1). Warm to the touch. Glows faintly near the house's creatures."),
    "voidcleaver greatsword":  ("2d6+2 slashing", "Heavy, two-handed. Cuts leave trails of darkness. +2 damage vs aberrations."),
    "hollowshot longbow":      ("1d8+2 piercing", "Ammunition, heavy, range 150/600 ft, two-handed. Arrows vanish mid-flight and reappear inside the target."),
    "aldric's paradox":        ("1d4+3 force",    "Finesse, light, thrown (20/60 ft). Exists in two states. On hit: WIS DC 15 or displaced 10 ft random direction. 1/long rest: cast Dimension Door (no slot)."),
    "soulcrusher maul":        ("1d8+2 bludgeoning", "Versatile (1d10+2). Pulses with trapped screams. On crit: target is stunned until end of their next turn."),
}

# Weapon rarity — used for colored embeds. Unlisted weapons are Common (gray).
WEAPON_RARITY = {
    "splinterfang hatchet":     ("Uncommon",  0x2ecc71),  # green
    "angle's edge":             ("Uncommon",  0x2ecc71),
    "longsword of the remnant": ("Uncommon",  0x2ecc71),
    "mirrorbane rapier":        ("Rare",      0x3498db),  # blue
    "voidcleaver greatsword":   ("Very Rare", 0x9b59b6),  # purple
    "hollowshot longbow":       ("Very Rare", 0x9b59b6),
    "aldric's paradox":         ("Legendary", 0xe67e22),  # orange
    "soulcrusher maul":         ("Very Rare", 0x9b59b6),  # purple
    "fractal wand":             ("Uncommon",  0x2ecc71),  # green
    "copycat shortbow":         ("Rare",      0x3498db),  # blue
    "echo staff":               ("Rare",      0x3498db),  # blue
    "mindbreak staff":          ("Very Rare", 0x9b59b6),  # purple
    "hungering blade":          ("Very Rare", 0x9b59b6),  # purple
    "tome of unmaking":         ("Very Rare", 0x9b59b6),  # purple
    "sword of testing":         ("Rare",      0x3498db),  # blue
    "shield of debugging":      ("Rare",      0x3498db),  # blue
    "helmet of feedback":       ("Uncommon",  0x2ecc71),  # green
    "tidecaller axe":           ("Uncommon",  0x2ecc71),
    "coral blade":              ("Rare",      0x3498db),
    "harpoon of the deep":      ("Rare",      0x3498db),
    "stormbreaker maul":        ("Very Rare", 0x9b59b6),
    "krakens tooth":            ("Very Rare", 0x9b59b6),
    "sigrids resolve":          ("Legendary", 0xe67e22),
}

# Campaign-specific armor: maps unique name → base armor type (for AC calculation)
CAMPAIGN_ARMOR = {
    "geometrist's hide": "hide",
    "echoweave leather": "studded leather",
    "voidtouched breastplate": "breastplate",
    "hollowplate": "half plate",
    "folded chain shirt": "chain shirt",
    "reflective chain": "chain shirt",
    "voidweave robes": "padded",
    "abyssal plate": "splint",
    "hollowhide leather": "studded leather",
    "shield of debugging": "shield",
    "helmet of feedback": "leather",
    "barnacle mail": "chain mail",
    "drowned leather": "studded leather",
    "kelpweave robes": "padded",
    "coral plate": "splint",
}

ARMOR_RARITY = {
    "geometrist's hide":        ("Uncommon",  0x2ecc71),  # green
    "echoweave leather":        ("Rare",      0x3498db),  # blue
    "voidtouched breastplate":  ("Very Rare", 0x9b59b6),  # purple
    "hollowplate":              ("Very Rare", 0x9b59b6),  # purple
    "folded chain shirt":       ("Uncommon",  0x2ecc71),  # green
    "reflective chain":         ("Rare",      0x3498db),  # blue
    "voidweave robes":          ("Very Rare", 0x9b59b6),  # purple
    "abyssal plate":            ("Very Rare", 0x9b59b6),  # purple
    "hollowhide leather":       ("Very Rare", 0x9b59b6),  # purple
    "shield of debugging":      ("Rare",      0x3498db),
    "helmet of feedback":       ("Uncommon",  0x2ecc71),
    "barnacle mail":            ("Uncommon",  0x2ecc71),
    "drowned leather":          ("Rare",      0x3498db),
    "kelpweave robes":          ("Rare",      0x3498db),
    "coral plate":              ("Very Rare", 0x9b59b6),
}

# Item → equipment slot mapping (items not listed default to "armor" for armor type, "weapon" for weapon type)
ITEM_SLOT = {
    "helmet of feedback": "head",
    "shield of debugging": "offhand",
    "sword of testing": "weapon",
    # Add more as items are created:
    # "ring of protection": "ring",
    # "gauntlets of ogre": "hands",
    # "boots of speed": "feet",
}

CLASS_WEAPON_PROF = {
    "Barbarian": ALL_WEAPONS, "Warrior": ALL_WEAPONS,
    "Paladin":   ALL_WEAPONS, "Ranger":  ALL_WEAPONS,
    "Cleric":    SIMPLE_WEAPONS,
    "Druid":     (SIMPLE_WEAPONS - {"handaxe"}) | {"quarterstaff","dagger","spear"},
    "Bard":      SIMPLE_WEAPONS | {"crossbow, light","longsword","rapier","shortsword"},
    "Rogue":     SIMPLE_WEAPONS | {"crossbow, light","longsword","rapier","shortsword"},
    "Warlock":   SIMPLE_WEAPONS, "Monk": SIMPLE_WEAPONS | {"shortsword"},
    "Necromancer": {"dagger","quarterstaff","crossbow, light"},
    "Deathknight": ALL_WEAPONS,
    "Sorcerer":  {"dagger","quarterstaff","crossbow, light"},
    "Wizard":    {"dagger","quarterstaff","crossbow, light"},
}

RACE_WEAPON_PROF = {
    "Elf":      {"longsword","shortsword","shortbow","longbow"},
    "Dwarf":    {"warhammer","handaxe","greataxe"},
    "Half-Elf": set(), "Dragonborn": set(), "Gnome": set(),
    "Halfling": set(), "Human": set(), "Half-Orc": set(), "Tiefling": set(),
}

CLASS_SCHOOLS = {
    "Barbarian":[],"Warrior":[],"Monk":[],"Rogue":[],
    "Deathknight":["Necromancy","Evocation","Abjuration"],
    "Bard":    ["Enchantment","Illusion","Transmutation","Divination","Conjuration","Evocation"],
    "Cleric":  ["Abjuration","Divination","Evocation","Necromancy","Transmutation"],
    "Druid":   ["Conjuration","Divination","Evocation","Transmutation","Abjuration"],
    "Necromancer":["Necromancy","Conjuration","Evocation","Abjuration"],
    "Paladin": ["Abjuration","Evocation","Divination"],
    "Ranger":  ["Conjuration","Divination","Transmutation","Evocation"],
    "Sorcerer":["Evocation","Transmutation","Conjuration","Enchantment","Illusion","Abjuration"],
    "Warlock": ["Enchantment","Illusion","Necromancy","Conjuration","Evocation","Abjuration"],
    "Wizard":  ["Abjuration","Conjuration","Divination","Enchantment","Evocation","Illusion","Necromancy","Transmutation"],
}

# Per-class spell lists (faithful to D&D 5e PHB). Only spells in SPELLS dict are shown.
CLASS_SPELL_LIST = {
    "Barbarian": [],
    "Warrior": [],
    "Monk": [],
    "Rogue": [],
    "Bard": [
        # Cantrips
        "blade ward", "dancing lights", "mending", "message", "minor illusion", "prestidigitation",
        "thunderclap", "vicious mockery",
        "guidance",
        # 1st
        "bane", "charm person", "color spray", "cure wounds", "detect magic", "dissonant whispers", "faerie fire", "healing word", "hellish rebuke", "hex", "sleep", "thunderwave", "command",
        # 2nd
        "blindness/deafness", "hold person", "invisibility", "misty step", "shatter",
        # 3rd
        "counterspell", "hypnotic pattern", "fly",
        # 4th
        "blight",
        # 5th
        "mass cure wounds",
    ],
    "Cleric": [
        # Cantrips
        "light", "sacred flame", "spare the dying", "toll the dead", "blade ward", "guidance",
        # 1st
        "bane", "bless", "command", "cure wounds", "detect magic", "guiding bolt", "healing word", "inflict wounds", "shield", "shield of faith",
        # 2nd
        "blindness/deafness", "hold person", "lesser restoration", "prayer of healing", "spiritual weapon",
        # 3rd
        "animate dead", "counterspell", "mass healing word", "spirit guardians",
        # 5th
        "mass cure wounds",
    ],
    "Druid": [
        # Cantrips
        "poison spray", "thorn whip", "produce flame", "druidcraft", "guidance",
        # 1st
        "cure wounds", "detect magic", "entangle", "faerie fire", "goodberry", "healing word", "thunderwave",
        # 2nd
        "hold person", "lesser restoration", "moonbeam", "spider climb",
        # 3rd
        "counterspell", "mass healing word",
        # 5th
        "mass cure wounds",
    ],
    "Necromancer": [
        # Cantrips
        "chill touch", "toll the dead",
        # 1st
        "false life", "magic missile", "shield", "witch bolt",
        # 2nd
        "blindness/deafness", "scorching ray",
        # 3rd
        "animate dead", "bestow curse", "counterspell", "fireball",
        # 4th
        "blight",
    ],
    "Paladin": [
        # 1st
        "bless", "command", "cure wounds", "detect magic", "divine smite", "shield", "shield of faith", "thunderwave",
        # 2nd
        "lesser restoration", "misty step", "prayer of healing",
        # 5th
        "mass cure wounds",
    ],
    "Ranger": [
        # 1st
        "cure wounds", "detect magic", "ensnaring strike", "healing word", "hunter's mark",
        # 2nd
        "misty step", "spider climb",
        # 3rd
        "lightning bolt",
    ],
    "Deathknight": [
        # Cantrips
        "chill touch", "toll the dead",
        # 1st
        "shield", "witch bolt",
        # 2nd
        "blindness/deafness", "hold person",
        # 3rd
        "animate dead", "counterspell",
        # 4th
        "blight",
    ],
    "Sorcerer": [
        # Cantrips
        "acid splash", "blade ward", "chill touch", "fire bolt", "ray of frost", "shocking grasp",
        # 1st
        "burning hands", "charm person", "detect magic", "false life", "mage armor", "magic missile", "shield", "sleep", "thunderwave",
        # 2nd
        "blindness/deafness", "hold person", "invisibility", "misty step", "scorching ray", "shatter",
        # 3rd
        "counterspell", "fireball", "fly", "hypnotic pattern", "lightning bolt",
        # 4th
        "blight",
        # 5th
        "mass cure wounds",
    ],
    "Warlock": [
        # Cantrips
        "blade ward", "chill touch", "eldritch blast", "poison spray", "toll the dead",
        # 1st
        "burning hands", "charm person", "false life", "hellish rebuke", "hex", "witch bolt",
        # 2nd
        "blindness/deafness", "hold person", "invisibility", "misty step", "scorching ray", "shatter",
        # 3rd
        "counterspell", "fireball", "fly", "hypnotic pattern",
        # 4th
        "blight",
        # 5th
        "mass cure wounds",
    ],
    "Wizard": [
        # Cantrips
        "acid splash", "blade ward", "chill touch", "fire bolt", "light", "poison spray", "ray of frost", "shocking grasp", "toll the dead",
        # 1st
        "burning hands", "charm person", "color spray", "detect magic", "false life", "mage armor", "magic missile", "shield", "sleep", "thunderwave", "witch bolt",
        # 2nd
        "blindness/deafness", "hold person", "invisibility", "misty step", "scorching ray", "shatter", "spider climb",
        # 3rd
        "animate dead", "counterspell", "fireball", "fly", "hypnotic pattern", "lightning bolt",
        # 4th
        "blight", "black tentacles",
        # 5th
        "mass cure wounds",
    ],
}

SPELLCASTING_STAT = {
    "Bard":"charisma","Cleric":"wisdom","Druid":"wisdom",
    "Necromancer":"intelligence",
    "Paladin":"charisma","Ranger":"wisdom","Deathknight":"charisma","Sorcerer":"charisma",
    "Warlock":"charisma","Wizard":"intelligence",
}

SCHOOL_GIF = {
    "Abjuration":"vfx/spell_vfx/dnd_conjuration.gif",
    "Conjuration":"vfx/spell_vfx/dnd_conjuration.gif",
    "Divination":"vfx/spell_vfx/dnd_divination.gif",
    "Enchantment":"vfx/spell_vfx/dnd_illusion.gif",
    "Evocation":"vfx/spell_vfx/dnd_evocation_fire.gif",
    "Illusion":"vfx/spell_vfx/dnd_illusion.gif",
    "Necromancy":"vfx/spell_vfx/dnd_necromancy.gif",
    "Transmutation":"vfx/spell_vfx/dnd_transmutation.gif",
}

# Per-spell gif overrides (takes priority over school gif)
SPELL_GIF_OVERRIDE = {
    "acid splash":"vfx/spell_vfx/dnd_acid_splash_conjuration.gif",
    "animate dead":"vfx/spell_vfx/dnd_animate_dead_necromancy.gif",
    "blight":"vfx/spell_vfx/dnd_blight_necromancy.gif",
    "charm person":"vfx/spell_vfx/dnd_charm_person_enchantment.gif",
    "chill touch":"vfx/spell_vfx/dnd_chill_touch_necromancy.gif",
    "command":"vfx/spell_vfx/dnd_command_enchantment.gif",
    "counterspell":"vfx/spell_vfx/dnd_counterspell_abjuration.gif",
    "detect magic":"vfx/spell_vfx/dnd_detect_magic_divination.gif",
    "eldritch blast":"vfx/spell_vfx/dnd_eldritch_blast_evocation.gif",
    "faerie fire":"vfx/spell_vfx/dnd_faerie_fire_evocation.gif",
    "fire bolt":"vfx/spell_vfx/dnd_fire_bolt_evocation.gif",
    "fireball":"vfx/spell_vfx/dnd_fireball_evocation.gif",
    "guidance":"vfx/spell_vfx/dnd_guidance_divintation.gif",
    "guiding bolt":"vfx/spell_vfx/dnd_guiding_bolt_evocation.gif",
    "healing word":"vfx/spell_vfx/dnd_healing_word_evocation.gif",
    "hold person":"vfx/spell_vfx/dnd_hold_person_enchantment.gif",
    "hypnotic pattern":"vfx/spell_vfx/dnd_hypnotic_pattern_illusion.gif",
    "inflict wounds":"vfx/spell_vfx/dnd_inflict_wounds_necromancy.gif",
    "invisibility":"vfx/spell_vfx/dnd_invisibility_illusion.gif",
    "mass cure wounds":"vfx/spell_vfx/dnd_mass_cure_wounds_evocation.gif",
    "mass healing word":"vfx/spell_vfx/dnd_mass_healing_word_evocation.gif",
    "mending":"vfx/spell_vfx/dnd_mending_transmutation.gif",
    "message":"vfx/spell_vfx/dnd_message_transmutation.gif",
    "minor illusion":"vfx/spell_vfx/dnd_minor_illusion_illusion.gif",
    "misty step":"vfx/spell_vfx/dnd_misty_step_conjuration.gif",
    "moonbeam":"vfx/spell_vfx/dnd_moonbeam_evocation.gif",
    "prayer of healing":"vfx/spell_vfx/dnd_prayer_of_healing_evocation.gif",
    "prestidigitation":"vfx/spell_vfx/dnd_prestidigitation_transmutation.gif",
    "produce flame":"vfx/spell_vfx/dnd_produce_flame_conjuration.gif",
    "sacred flame":"vfx/spell_vfx/dnd_sacred_flame_evocation.gif",
    "shield":"vfx/spell_vfx/dnd_shield_abjuration.gif",
    "shocking grasp":"vfx/spell_vfx/dnd_shocking_grasp_evocation.gif",
    "sleep":"vfx/spell_vfx/dnd_sleep_enchantment.gif",
    "spirit guardians":"vfx/spell_vfx/dnd_spirit_guardians_conjuration.gif",
    "spiritual weapon":"vfx/spell_vfx/dnd_spiritual_weapon_evocation.gif",
    "vicious mockery":"vfx/spell_vfx/dnd_vicious_mockery_enchantment.gif",
    "lightning bolt":"vfx/spell_vfx/dnd_lightning_conjuration.gif",
    "magic missile":"vfx/spell_vfx/dnd_magic_missile_evocation.gif",
    "hunter's mark":"vfx/spell_vfx/dnd_hunters_mark_divination.gif",
    "thunderwave":"vfx/spell_vfx/dnd_thunder_wave_evocation.gif",
    "blindness/deafness":"vfx/spell_vfx/dnd_blindness_deafness_necromancy.gif",
    "dancing lights":"vfx/spell_vfx/dnd_dancing_lights_evocation.gif",
    "entangle":"vfx/spell_vfx/dnd_entangle_conjuration.gif",
    "lesser restoration":"vfx/spell_vfx/dnd_lesser_restoration_abjuration.gif",
    "scorching ray":"vfx/spell_vfx/dnd_scorching_ray_evocation.gif",
    "shatter":"vfx/spell_vfx/dnd_shatter_evocation.gif",
    "spider climb":"vfx/spell_vfx/dnd_spider_climb_transmutation.gif",
    "cure wounds":"vfx/spell_vfx/dnd_cure_wounds_evocation.gif",
    "druidcraft":"vfx/spell_vfx/dnd_druidcraft_transmutation.gif",
    "fly":"vfx/spell_vfx/dnd_fly_transmutation.gif",
    "witch bolt":"vfx/spell_vfx/dnd_witch_bolt_evocation.gif",
    "bless":"vfx/spell_vfx/dnd_bless_enchantment.gif",
    "bane":"vfx/spell_vfx/dnd_bane_enchantment.gif",
    "mage armor":"vfx/spell_vfx/dnd_mage_armor_abjuration.gif",
    "false life":"vfx/spell_vfx/dnd_false_life_necromancy.gif",
    "hellish rebuke":"vfx/spell_vfx/dnd_hellish_rebuke_evocation.gif",
    "color spray":"vfx/spell_vfx/dnd_color_spray_illusion.gif",
    "goodberry":"vfx/spell_vfx/dnd_goodberry_transmutation.gif",
    "shield of faith":"vfx/spell_vfx/dnd_shield_of_faith_abjuration.gif",
    "barkskin":"vfx/spell_vfx/dnd_barkskin_transmutation.gif",
    "heat metal":"vfx/spell_vfx/dnd_heat_metal_transmutation.gif",
    "web":"vfx/spell_vfx/dnd_web_conjuration.gif",
    "silence":"vfx/spell_vfx/dnd_silence_illusion.gif",
    "dispel magic":"vfx/spell_vfx/dnd_dispel_magic_abjuration.gif",
    "fear":"vfx/spell_vfx/dnd_fear_illusion.gif",
    "haste":"vfx/spell_vfx/dnd_haste_transmutation.gif",
    "bestow curse":"vfx/spell_vfx/dnd_bestow_curse_necromancy.gif",
    "polymorph":"vfx/spell_vfx/dnd_polymorph_transmutation.gif",
    "banishment":"vfx/spell_vfx/dnd_banishment_abjuration.gif",
    "ice storm":"vfx/spell_vfx/dnd_ice_storm_evocation.gif",
    "cone of cold":"vfx/spell_vfx/dnd_cone_of_cold_evocation.gif",
    "ray of frost":"vfx/spell_vfx/dnd_ray_of_frost_evocation.gif",
    "poison spray":"vfx/spell_vfx/dnd_poison_spray_conjuration.gif",
    "light":"vfx/spell_vfx/dnd_light_evocation.gif",
    "spare the dying":"vfx/spell_vfx/dnd_spare_the_dying_necromancy.gif",
    "black tentacles":"vfx/spell_vfx/dnd_black_tentacles_conjuration.gif",
}

# School fallback is no longer used for castable spells (all have overrides above)
# but kept for any future spells added without an override

SPELLS = {
    "acid splash":        ("Cantrip","Conjuration","60 ft","1d6 acid. DEX save or take damage."),
    "blade ward":         ("Cantrip","Abjuration","Self","Resistance to bludgeoning/piercing/slashing until end of next turn."),
    "chill touch":        ("Cantrip","Necromancy","120 ft","1d8 necrotic. Target can't regain HP until your next turn."),
    "fire bolt":          ("Cantrip","Evocation","120 ft","1d10 fire damage. Ranged spell attack."),
    "sacred flame":       ("Cantrip","Evocation","60 ft","1d8 radiant. DEX save or take damage."),
    "shocking grasp":     ("Cantrip","Evocation","Touch","1d8 lightning. Target can't take reactions until its next turn."),
    "toll the dead":      ("Cantrip","Necromancy","60 ft","1d8 necrotic (1d12 if target is missing HP). WIS save."),
    "eldritch blast":     ("Cantrip","Evocation","120 ft","1d10 force. Extra beams at levels 5, 11, 17."),
    "burning hands":      ("1st","Evocation","Self (15-ft cone)","3d6 fire. DEX save for half."),
    "charm person":       ("1st","Enchantment","30 ft","Charm a humanoid. WIS save. Concentration, 1 hour."),
    "cure wounds":        ("1st","Evocation","Touch","Restore 1d8 + spellcasting modifier HP."),
    "detect magic":       ("1st","Divination","Self","Sense magic within 30 ft for 10 min. Concentration."),
    "healing word":       ("1st","Evocation","60 ft","Bonus action. Restore 1d4 + spellcasting modifier HP."),
    "hex":                ("1st","Enchantment","90 ft","Curse a target. Extra 1d6 necrotic on attacks. Concentration."),
    "magic missile":      ("1st","Evocation","120 ft","Three darts, 1d4+1 force each. Always hits."),
    "shield":             ("1st","Abjuration","Self","+5 AC reaction until next turn. Immune to Magic Missile."),
    "sleep":              ("1st","Enchantment","90 ft","Put creatures to sleep (5d8 HP worth). No save."),
    "thunderwave":        ("1st","Evocation","Self (15-ft cube)","2d8 thunder + pushed 10 ft. CON save for half."),
    "witch bolt":         ("1st","Evocation","30 ft","1d12 lightning on hit. Sustain each turn as bonus action. Concentration."),
    "blindness/deafness": ("2nd","Necromancy","30 ft","Blind or deafen a creature. CON save each turn to end."),
    "hold person":        ("2nd","Enchantment","60 ft","Paralyze a humanoid. WIS save each turn. Concentration."),
    "invisibility":       ("2nd","Illusion","Touch","Target becomes invisible until it attacks or casts. Concentration."),
    "misty step":         ("2nd","Conjuration","Self","Bonus action. Teleport up to 30 ft."),
    "scorching ray":      ("2nd","Evocation","120 ft","Three rays, each 2d6 fire. Ranged spell attack per ray."),
    "shatter":            ("2nd","Evocation","60 ft","3d8 thunder in 10-ft sphere. CON save for half."),
    "spider climb":       ("2nd","Transmutation","Touch","Target can climb any surface for 1 hour. Concentration."),
    "counterspell":       ("3rd","Abjuration","60 ft","Reaction. Auto-stops spells ≤3rd level."),
    "fireball":           ("3rd","Evocation","150 ft","8d6 fire in 20-ft radius. DEX save for half."),
    "fly":                ("3rd","Transmutation","Touch","Target gains 60 ft fly speed for 10 min. Concentration."),
    "hypnotic pattern":   ("3rd","Illusion","120 ft","Creatures in 30-ft cube are incapacitated. WIS save. Concentration."),
    "lightning bolt":     ("3rd","Evocation","Self (100-ft line)","8d6 lightning. DEX save for half."),
    "mass cure wounds":   ("5th","Evocation","60 ft","Up to 6 creatures regain 3d8 + spellcasting modifier HP."),
    "prayer of healing":  ("2nd","Evocation","30 ft","Up to 6 creatures regain 2d8 + spellcasting modifier HP. 10 min cast."),
    "animate dead":       ("3rd","Necromancy","10 ft","Raise a skeleton or zombie from a corpse."),
    "blight":             ("4th","Necromancy","30 ft","8d8 necrotic. CON save for half. Plants auto-fail."),
    # ── New spells ─────────────────────────────────────────────────────────────
    "vicious mockery":    ("Cantrip","Enchantment","60 ft","1d4 psychic. WIS save or disadvantage on next attack."),
    "minor illusion":     ("Cantrip","Illusion","30 ft","Create a sound or image. Investigation DC = spell DC to discern."),
    "prestidigitation":   ("Cantrip","Transmutation","10 ft","Minor magical trick. Light, clean, warm, flavor, mark, trinket."),
    "message":            ("Cantrip","Transmutation","120 ft","Whisper a message to a creature. They can reply."),
    "mending":            ("Cantrip","Transmutation","Touch","Repair a single break or tear in an object."),
    "dancing lights":     ("Cantrip","Evocation","120 ft","Create up to 4 torch-sized lights. Concentration, 1 min."),
    "thorn whip":         ("Cantrip","Transmutation","30 ft","1d6 piercing. Pull target 10 ft toward you."),
    "produce flame":      ("Cantrip","Conjuration","Self","1d8 fire. Can hurl as ranged spell attack."),
    "druidcraft":         ("Cantrip","Transmutation","30 ft","Minor nature effect. Predict weather, bloom flower, sensory effect."),
    "guidance":           ("Cantrip","Divination","Touch","Target adds 1d4 to one ability check. Concentration."),
    "thunderclap":        ("Cantrip","Evocation","5 ft","1d6 thunder to all creatures within 5 ft. CON save."),
    "dissonant whispers": ("1st","Enchantment","60 ft","3d6 psychic. WIS save or must use reaction to move away."),
    "faerie fire":        ("1st","Evocation","60 ft","Creatures in 20-ft cube outlined. DEX save or attacks have advantage."),
    "hunter's mark":      ("1st","Divination","90 ft","+1d6 damage to marked target. Concentration, 1 hour."),
    "entangle":           ("1st","Conjuration","90 ft","20-ft square. STR save or restrained. Concentration."),
    "command":            ("1st","Enchantment","60 ft","One word command. WIS save or obey (Approach, Drop, Flee, Grovel, Halt)."),
    "guiding bolt":       ("1st","Evocation","120 ft","4d6 radiant. Next attack vs target has advantage."),
    "inflict wounds":     ("1st","Necromancy","Touch","3d10 necrotic. Melee spell attack."),
    "moonbeam":           ("2nd","Evocation","120 ft","2d10 radiant in 5-ft cylinder. CON save for half. Concentration."),
    "spiritual weapon":   ("2nd","Evocation","60 ft","1d8+mod force. Bonus action attack each turn. No concentration."),
    "ensnaring strike":   ("1st","Conjuration","Self","Next hit: STR save or restrained + 1d6 piercing/turn."),
    "divine smite":       ("1st","Evocation","Self","On hit: +2d8 radiant (+1d8 per slot above 1st, +1d8 vs undead)."),
    "spirit guardians":   ("3rd","Conjuration","Self (15-ft radius)","3d8 radiant/necrotic. WIS save for half. Concentration."),
    "mass healing word":  ("3rd","Evocation","60 ft","Up to 6 creatures regain 1d4 + mod HP."),
    "lesser restoration": ("2nd","Abjuration","Touch","End one disease or condition: blinded, deafened, paralyzed, or poisoned."),
    "bless":              ("1st","Enchantment","30 ft","+1d4 to attacks and saves for up to 3 creatures. Concentration."),
    "bane":               ("1st","Enchantment","30 ft","Up to 3 creatures subtract 1d4 from attacks and saves. CHA save. Concentration."),
    "mage armor":         ("1st","Abjuration","Touch","AC becomes 13 + DEX mod. 8 hours, no concentration."),
    "false life":         ("1st","Necromancy","Self","Gain 1d4+4 temp HP. 1 hour."),
    "hellish rebuke":     ("1st","Evocation","60 ft","Reaction: 2d10 fire to creature that hit you. DEX save for half."),
    "color spray":        ("1st","Illusion","Self (15-ft cone)","6d10 HP of creatures blinded. Lowest HP affected first."),
    "goodberry":          ("1st","Transmutation","Touch","Create 10 berries. Each heals 1 HP when eaten."),
    "shield of faith":    ("1st","Abjuration","60 ft","+2 AC to target. Concentration, 10 min."),
    "barkskin":           ("2nd","Transmutation","Touch","Target AC can't be less than 16. Concentration, 1 hour."),
    "heat metal":         ("2nd","Transmutation","60 ft","2d8 fire to creature wearing/holding metal. Bonus action repeat. Concentration."),
    "web":                ("2nd","Conjuration","60 ft","20-ft cube. DEX save or restrained. Flammable. Concentration."),
    "silence":            ("2nd","Illusion","120 ft","20-ft radius sphere. No sound. Blocks verbal spells. Concentration."),
    "dispel magic":       ("3rd","Abjuration","120 ft","End one spell on target. Auto for 3rd or lower; check for higher."),
    "fear":               ("3rd","Illusion","Self (30-ft cone)","WIS save or frightened + must dash away. Concentration."),
    "haste":              ("3rd","Transmutation","30 ft","+2 AC, double speed, extra action. Concentration, 1 min."),
    "bestow curse":       ("3rd","Necromancy","Touch","WIS save or cursed. Many options. Concentration."),
    "polymorph":          ("4th","Transmutation","60 ft","Transform creature into beast. WIS save if unwilling. Concentration."),
    "banishment":         ("4th","Abjuration","60 ft","CHA save or banished to another plane. Concentration, 1 min."),
    "ice storm":          ("4th","Evocation","300 ft","2d8 bludgeoning + 4d6 cold in 20-ft radius. DEX save for half."),
    "cone of cold":       ("5th","Evocation","Self (60-ft cone)","8d8 cold. CON save for half."),
    "ray of frost":       ("Cantrip","Evocation","60 ft","1d8 cold. Speed reduced by 10 ft until next turn."),
    "poison spray":       ("Cantrip","Conjuration","10 ft","1d12 poison. CON save or take damage."),
    "light":              ("Cantrip","Evocation","Touch","Object sheds bright light 20 ft, dim 20 ft. 1 hour."),
    "spare the dying":    ("Cantrip","Necromancy","Touch","Stabilize a creature at 0 HP."),
    "black tentacles":    ("4th","Conjuration","90 ft","20-ft square. DEX save or restrained + 3d6 bludgeoning/turn. Concentration."),
}

CASTABLE_SPELLS = {
    "fire bolt":       {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d10","heal":None,  "slot":0,"upcast":None},
    "eldritch blast":  {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d10","heal":None,  "slot":0,"upcast":None},
    "chill touch":     {"school":"Necromancy", "cast_type":"attack","save_stat":None,  "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "shocking grasp":  {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "sacred flame":    {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "toll the dead":   {"school":"Necromancy", "cast_type":"save",  "save_stat":"WIS", "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "burning hands":   {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"3d6", "heal":None,  "slot":1,"upcast":"1d6"},
    "magic missile":   {"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":"3d4+3","heal":None, "slot":1,"upcast":"1d4+1"},
    "thunderwave":     {"school":"Evocation",  "cast_type":"save",  "save_stat":"CON", "damage":"2d8", "heal":None,  "slot":1,"upcast":"1d8"},
    "witch bolt":      {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d12","heal":None,  "slot":1,"upcast":"1d12"},
    "cure wounds":     {"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":"1d8", "slot":1,"upcast":"1d8"},
    "healing word":    {"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":"1d4", "slot":1,"upcast":"1d4"},
    "sleep":           {"school":"Enchantment","cast_type":"auto",  "save_stat":None,  "damage":"5d8", "heal":None,  "slot":1,"upcast":"2d8"},
    "shield":          {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "hex":             {"school":"Enchantment","cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "scorching ray":   {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"2d6", "heal":None,  "slot":2,"upcast":"2d6"},
    "shatter":         {"school":"Evocation",  "cast_type":"save",  "save_stat":"CON", "damage":"3d8", "heal":None,  "slot":2,"upcast":"1d8"},
    "hold person":     {"school":"Enchantment","cast_type":"save",  "save_stat":"WIS", "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "misty step":      {"school":"Conjuration","cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "prayer of healing":{"school":"Evocation", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":"2d8", "slot":2,"upcast":"1d8"},
    "counterspell":    {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "fireball":        {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"8d6", "heal":None,  "slot":3,"upcast":"1d6"},
    "lightning bolt":  {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"8d6", "heal":None,  "slot":3,"upcast":"1d6"},
    "animate dead":    {"school":"Necromancy", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "mass cure wounds":{"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":"3d8", "slot":5,"upcast":"1d8"},
    "blight":          {"school":"Necromancy", "cast_type":"save",  "save_stat":"CON", "damage":"8d8", "heal":None,  "slot":4,"upcast":"2d8"},
    # ── New castable spells ────────────────────────────────────────────────────
    "vicious mockery":   {"school":"Enchantment","cast_type":"save",  "save_stat":"WIS", "damage":"1d4", "heal":None,  "slot":0,"upcast":None},
    "thorn whip":        {"school":"Transmutation","cast_type":"attack","save_stat":None, "damage":"1d6", "heal":None,  "slot":0,"upcast":None},
    "produce flame":     {"school":"Conjuration","cast_type":"attack","save_stat":None,  "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "thunderclap":       {"school":"Evocation",  "cast_type":"save",  "save_stat":"CON", "damage":"1d6", "heal":None,  "slot":0,"upcast":None},
    "dissonant whispers":{"school":"Enchantment","cast_type":"save",  "save_stat":"WIS", "damage":"3d6", "heal":None,  "slot":1,"upcast":"1d6"},
    "guiding bolt":      {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"4d6", "heal":None,  "slot":1,"upcast":"1d6"},
    "inflict wounds":    {"school":"Necromancy", "cast_type":"attack","save_stat":None,  "damage":"3d10","heal":None,  "slot":1,"upcast":"1d10"},
    "hunter's mark":     {"school":"Divination", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "faerie fire":       {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "entangle":          {"school":"Conjuration","cast_type":"save",  "save_stat":"STR", "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "command":           {"school":"Enchantment","cast_type":"save",  "save_stat":"WIS", "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "ensnaring strike":  {"school":"Conjuration","cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "divine smite":      {"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":"2d8", "heal":None,  "slot":1,"upcast":"1d8"},
    "moonbeam":          {"school":"Evocation",  "cast_type":"save",  "save_stat":"CON", "damage":"2d10","heal":None,  "slot":2,"upcast":"1d10"},
    "spiritual weapon":  {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d8", "heal":None,  "slot":2,"upcast":None},
    "spirit guardians":  {"school":"Conjuration","cast_type":"save",  "save_stat":"WIS", "damage":"3d8", "heal":None,  "slot":3,"upcast":"1d8"},
    "mass healing word": {"school":"Evocation",  "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":"1d4", "slot":3,"upcast":"1d4"},
    "lesser restoration":  {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "ray of frost":    {"school":"Evocation",  "cast_type":"attack","save_stat":None,  "damage":"1d8", "heal":None,  "slot":0,"upcast":None},
    "poison spray":    {"school":"Conjuration","cast_type":"save",  "save_stat":"CON", "damage":"1d12","heal":None,  "slot":0,"upcast":None},
    "spare the dying": {"school":"Necromancy", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":0,"upcast":None},
    "hellish rebuke":  {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"2d10","heal":None,  "slot":1,"upcast":"1d10"},
    "false life":      {"school":"Necromancy", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "color spray":     {"school":"Illusion",   "cast_type":"auto",  "save_stat":None,  "damage":"6d10","heal":None,  "slot":1,"upcast":"2d10"},
    "goodberry":       {"school":"Transmutation","cast_type":"auto","save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "bane":            {"school":"Enchantment","cast_type":"save",  "save_stat":"CHA", "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "mage armor":      {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "shield of faith": {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":1,"upcast":None},
    "heat metal":      {"school":"Transmutation","cast_type":"save","save_stat":"CON", "damage":"2d8", "heal":None,  "slot":2,"upcast":"1d8"},
    "web":             {"school":"Conjuration","cast_type":"save",  "save_stat":"DEX", "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "silence":         {"school":"Illusion",   "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "barkskin":        {"school":"Transmutation","cast_type":"auto","save_stat":None,  "damage":None,  "heal":None,  "slot":2,"upcast":None},
    "dispel magic":    {"school":"Abjuration", "cast_type":"auto",  "save_stat":None,  "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "fear":            {"school":"Illusion",   "cast_type":"save",  "save_stat":"WIS", "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "haste":           {"school":"Transmutation","cast_type":"auto","save_stat":None,  "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "bestow curse":    {"school":"Necromancy", "cast_type":"save",  "save_stat":"WIS", "damage":None,  "heal":None,  "slot":3,"upcast":None},
    "ice storm":       {"school":"Evocation",  "cast_type":"save",  "save_stat":"DEX", "damage":"2d8", "heal":None,  "slot":4,"upcast":"1d8"},
    "banishment":      {"school":"Abjuration", "cast_type":"save",  "save_stat":"CHA", "damage":None,  "heal":None,  "slot":4,"upcast":None},
    "polymorph":       {"school":"Transmutation","cast_type":"save","save_stat":"WIS", "damage":None,  "heal":None,  "slot":4,"upcast":None},
    "black tentacles": {"school":"Conjuration","cast_type":"save",  "save_stat":"DEX", "damage":"3d6", "heal":None,  "slot":4,"upcast":None},
    "cone of cold":    {"school":"Evocation",  "cast_type":"save",  "save_stat":"CON", "damage":"8d8", "heal":None,  "slot":5,"upcast":"1d8"},
}

CONDITIONS = {
    "blinded":      "Can't see. Attacks against you have advantage. Your attacks have disadvantage.",
    "charmed":      "Can't attack the charmer. Charmer has advantage on social checks against you.",
    "deafened":     "Can't hear. Auto-fails hearing checks.",
    "exhaustion":   "1=disadv checks, 2=speed halved, 3=disadv attacks/saves, 4=HP max halved, 5=speed 0, 6=death.",
    "frightened":   "Disadvantage on checks/attacks while source is visible. Can't move closer.",
    "grappled":     "Speed 0. Ends if grappler is incapacitated.",
    "incapacitated":"Can't take actions or reactions.",
    "invisible":    "Can't be seen. Your attacks have advantage. Attacks against you have disadvantage.",
    "paralyzed":    "Incapacitated, can't move/speak. Auto-fail STR/DEX saves. Hits within 5 ft are crits.",
    "petrified":    "Turned to stone. Incapacitated. Resistance to all damage.",
    "poisoned":     "Disadvantage on attack rolls and ability checks.",
    "prone":        "Disadvantage on attacks. Melee attacks against you have advantage; ranged have disadvantage.",
    "restrained":   "Speed 0. Attack disadv. DEX save disadv. Attacks against you have advantage.",
    "stunned":      "Incapacitated, can't move. Auto-fail STR/DEX saves. Attacks against you have advantage.",
    "unconscious":  "Incapacitated, can't move/speak. Auto-fail STR/DEX saves. Hits within 5 ft are crits.",
}

BACKGROUND_INFO = {
    "acolyte":    ("Insight, Religion",          "Two languages",              "Shelter of the Faithful"),
    "criminal":   ("Deception, Stealth",          "Thieves' tools, gaming set", "Criminal Contact"),
    "folk hero":  ("Animal Handling, Survival",   "Artisan's tools, vehicles",  "Rustic Hospitality"),
    "noble":      ("History, Persuasion",          "Gaming set, language",       "Position of Privilege"),
    "outlander":  ("Athletics, Survival",          "Musical instrument, language","Wanderer"),
    "sage":       ("Arcana, History",              "Two languages",              "Researcher"),
    "soldier":    ("Athletics, Intimidation",      "Gaming set, vehicles",       "Military Rank"),
    "charlatan":  ("Deception, Sleight of Hand",   "Disguise kit, forgery kit",  "False Identity"),
    "entertainer":("Acrobatics, Performance",      "Disguise kit, instrument",   "By Popular Demand"),
    "hermit":     ("Medicine, Religion",           "Herbalism kit, language",    "Discovery"),
}

STAT_FOR_SAVE = {
    "strength":"strength","str":"strength","dexterity":"dexterity","dex":"dexterity",
    "constitution":"constitution","con":"constitution","intelligence":"intelligence","int":"intelligence",
    "wisdom":"wisdom","wis":"wisdom","charisma":"charisma","cha":"charisma",
}

# Saving throw proficiencies per class
CLASS_SAVE_PROFS = {
    "Barbarian": {"strength","constitution"},
    "Bard":      {"dexterity","charisma"},
    "Cleric":    {"wisdom","charisma"},
    "Druid":     {"intelligence","wisdom"},
    "Warrior":   {"strength","constitution"},
    "Monk":      {"strength","dexterity"},
    "Necromancer":{"intelligence","wisdom"},
    "Paladin":   {"wisdom","charisma"},
    "Ranger":    {"strength","dexterity"},
    "Rogue":     {"dexterity","intelligence"},
    "Deathknight":{"strength","charisma"},
    "Sorcerer":  {"constitution","charisma"},
    "Warlock":   {"wisdom","charisma"},
    "Wizard":    {"intelligence","wisdom"},
}

# Class resources: name -> (max_formula, rest_type)
# max_formula is a lambda(level) -> int
CLASS_RESOURCES = {
    "Barbarian": [("Rage",          lambda lvl: 2 if lvl < 3 else 3 if lvl < 6 else 4 if lvl < 12 else 5 if lvl < 17 else 6, "long")],
    "Bard":      [("Bardic Inspiration", lambda lvl: max(1, modifier(lvl)), "short")],  # uses CHA mod, handled at runtime
    "Cleric":    [("Channel Divinity",   lambda lvl: 1 if lvl < 6 else 2 if lvl < 18 else 3, "short")],
    "Druid":     [],
    "Warrior":   [("Action Surge",       lambda lvl: 1 if lvl < 17 else 2, "short"),
                  ("Second Wind",        lambda lvl: 1, "short")],
    "Monk":      [("Ki Points",          lambda lvl: lvl, "short")],
    "Necromancer":[("Soul Shards",        lambda lvl: lvl, "long")],
    "Paladin":   [("Lay on Hands",       lambda lvl: lvl * 5, "long"),
                  ("Channel Divinity",   lambda lvl: 1, "short")],
    "Ranger":    [],
    "Rogue":     [],
    "Deathknight":[("Dark Pact",     lambda lvl: max(1, lvl // 2), "long")],
    "Sorcerer":  [("Sorcery Points",     lambda lvl: lvl, "long")],
    "Warlock":   [],
    "Wizard":    [("Arcane Recovery",    lambda lvl: max(1, lvl // 2), "long")],
}

# Sneak attack dice by Rogue level
SNEAK_ATTACK_DICE = {lvl: (lvl + 1) // 2 for lvl in range(1, 21)}

# Class features by level
CLASS_FEATURES = {
    "Barbarian": {
        1: ["Rage (2/long rest, +2 dmg)", "Unarmored Defense (AC = 10 + DEX + CON)"],
        2: ["Reckless Attack", "Danger Sense (ADV on DEX saves vs visible threats)"],
        3: ["Primal Path (subclass)"],
        4: ["ASI"],
        5: ["Extra Attack", "Fast Movement (+10 ft speed)"],
        7: ["Feral Instinct (ADV on initiative, act while surprised)"],
        8: ["ASI"],
        9: ["Brutal Critical (1 extra crit die)"],
        11: ["Relentless Rage (DC 10 CON save to stay at 1 HP)"],
        12: ["ASI"],
        15: ["Persistent Rage (only ends if unconscious or willing)"],
        16: ["ASI"],
        17: ["Brutal Critical (2 extra crit dice)"],
        19: ["ASI"],
        20: ["Primal Champion (+4 STR, +4 CON)"],
    },
    "Bard": {
        1: ["Bardic Inspiration (d6)", "Spellcasting"],
        2: ["Jack of All Trades (+half prof to unproficient checks)", "Song of Rest (d6)"],
        3: ["Bard College (subclass)", "Expertise (double prof on 2 skills)"],
        4: ["ASI"],
        5: ["Bardic Inspiration (d8)", "Font of Inspiration (recover on short rest)"],
        6: ["Countercharm", "Bard College feature"],
        8: ["ASI"],
        10: ["Bardic Inspiration (d10)", "Expertise (2 more skills)", "Magical Secrets (2 spells any class)"],
        12: ["ASI"],
        14: ["Magical Secrets (2 more spells)", "Bard College feature"],
        15: ["Bardic Inspiration (d12)"],
        16: ["ASI"],
        18: ["Magical Secrets (2 more spells)"],
        19: ["ASI"],
        20: ["Superior Inspiration (min 1 Bardic Inspiration on initiative)"],
    },
    "Cleric": {
        1: ["Spellcasting", "Divine Domain (subclass)", "Domain Spells"],
        2: ["Channel Divinity (1/rest)", "Domain feature"],
        4: ["ASI"],
        5: ["Destroy Undead (CR 1/2)"],
        6: ["Channel Divinity (2/rest)", "Domain feature"],
        8: ["ASI", "Destroy Undead (CR 1)", "Domain feature"],
        10: ["Divine Intervention"],
        11: ["Destroy Undead (CR 2)"],
        12: ["ASI"],
        14: ["Destroy Undead (CR 3)"],
        16: ["ASI"],
        17: ["Destroy Undead (CR 4)", "Domain feature"],
        18: ["Channel Divinity (3/rest)"],
        19: ["ASI"],
        20: ["Divine Intervention (auto-success)"],
    },
    "Druid": {
        1: ["Druidic", "Spellcasting"],
        2: ["Wild Shape (CR 1/4)", "Druid Circle (subclass)"],
        4: ["ASI", "Wild Shape (CR 1/2, swim speed)"],
        5: [],
        6: ["Circle feature"],
        8: ["ASI", "Wild Shape (CR 1, fly speed)"],
        10: ["Circle feature"],
        12: ["ASI"],
        14: ["Circle feature"],
        16: ["ASI"],
        18: ["Timeless Body", "Beast Spells (cast while Wild Shaped)"],
        19: ["ASI"],
        20: ["Archdruid (unlimited Wild Shape)"],
    },
    "Warrior": {
        1: ["Fighting Style", "Second Wind (1d10+level HP, 1/short rest)"],
        2: ["Action Surge (1/short rest)"],
        3: ["Martial Archetype (subclass)"],
        4: ["ASI"],
        5: ["Extra Attack"],
        6: ["ASI"],
        7: ["Archetype feature"],
        8: ["ASI"],
        9: ["Indomitable (reroll failed save, 1/long rest)"],
        10: ["Archetype feature"],
        11: ["Extra Attack (2)"],
        12: ["ASI"],
        13: ["Indomitable (2/long rest)"],
        14: ["ASI"],
        15: ["Archetype feature"],
        16: ["ASI"],
        17: ["Action Surge (2/short rest)", "Indomitable (3/long rest)"],
        18: ["Archetype feature"],
        19: ["ASI"],
        20: ["Extra Attack (3)"],
    },
    "Monk": {
        1: ["Unarmored Defense (AC = 10 + DEX + WIS)", "Martial Arts (d4)"],
        2: ["Ki Points", "Flurry of Blows", "Patient Defense", "Step of the Wind", "Unarmored Movement (+10 ft)"],
        3: ["Monastic Tradition (subclass)", "Deflect Missiles"],
        4: ["ASI", "Slow Fall"],
        5: ["Extra Attack", "Stunning Strike", "Martial Arts (d6)"],
        6: ["Ki-Empowered Strikes", "Tradition feature", "Unarmored Movement (+15 ft)"],
        7: ["Evasion", "Stillness of Mind"],
        8: ["ASI"],
        9: ["Unarmored Movement (+15 ft, walk on surfaces)"],
        10: ["Purity of Body", "Unarmored Movement (+20 ft)"],
        11: ["Tradition feature", "Martial Arts (d8)"],
        12: ["ASI"],
        13: ["Tongue of the Sun and Moon"],
        14: ["Diamond Soul (prof on all saves)", "Unarmored Movement (+25 ft)"],
        15: ["Timeless Body"],
        16: ["ASI"],
        17: ["Tradition feature", "Martial Arts (d10)"],
        18: ["Empty Body (invisible 1 min, 4 ki)", "Unarmored Movement (+30 ft)"],
        19: ["ASI"],
        20: ["Perfect Self (regain 4 ki on initiative if 0)"],
    },
    "Paladin": {
        1: ["Divine Sense", "Lay on Hands (5×level HP pool)"],
        2: ["Fighting Style", "Spellcasting", "Divine Smite"],
        3: ["Divine Health", "Sacred Oath (subclass)", "Channel Divinity"],
        4: ["ASI"],
        5: ["Extra Attack"],
        6: ["Aura of Protection (+CHA to saves within 10 ft)"],
        7: ["Oath feature"],
        8: ["ASI"],
        9: [],
        10: ["Aura of Courage (immune to frightened within 10 ft)"],
        11: ["Improved Divine Smite (+1d8 radiant on all melee hits)"],
        12: ["ASI"],
        14: ["Cleansing Touch (end spell on creature, CHA/long rest)"],
        15: ["Oath feature"],
        16: ["ASI"],
        17: [],
        18: ["Aura improvements (30 ft range)"],
        19: ["ASI"],
        20: ["Oath feature (capstone)"],
    },
    "Ranger": {
        1: ["Favored Enemy", "Natural Explorer"],
        2: ["Fighting Style", "Spellcasting"],
        3: ["Ranger Archetype (subclass)", "Primeval Awareness"],
        4: ["ASI"],
        5: ["Extra Attack"],
        6: ["Favored Enemy (2nd)", "Natural Explorer (2nd)"],
        7: ["Archetype feature"],
        8: ["ASI", "Land's Stride"],
        9: [],
        10: ["Natural Explorer (3rd)", "Hide in Plain Sight"],
        11: ["Archetype feature"],
        12: ["ASI"],
        13: [],
        14: ["Favored Enemy (3rd)", "Vanish"],
        15: ["Archetype feature"],
        16: ["ASI"],
        17: [],
        18: ["Feral Senses"],
        19: ["ASI"],
        20: ["Foe Slayer (+WIS to attack or damage vs favored enemy)"],
    },
    "Rogue": {
        1: ["Expertise (2 skills)", "Sneak Attack (1d6)", "Thieves' Cant"],
        2: ["Cunning Action (Dash/Disengage/Hide as bonus action)"],
        3: ["Roguish Archetype (subclass)", "Sneak Attack (2d6)"],
        4: ["ASI"],
        5: ["Uncanny Dodge (halve one attack's damage as reaction)", "Sneak Attack (3d6)"],
        6: ["Expertise (2 more skills)"],
        7: ["Evasion (no damage on DEX save success)", "Sneak Attack (4d6)"],
        8: ["ASI"],
        9: ["Archetype feature", "Sneak Attack (5d6)"],
        10: ["ASI"],
        11: ["Reliable Talent (min 10 on proficient checks)", "Sneak Attack (6d6)"],
        12: ["ASI"],
        13: ["Archetype feature", "Sneak Attack (7d6)"],
        14: ["Blindsense (10 ft)"],
        15: ["Slippery Mind (prof in WIS saves)", "Sneak Attack (8d6)"],
        16: ["ASI"],
        17: ["Archetype feature", "Sneak Attack (9d6)"],
        18: ["Elusive (no advantage on attacks against you)"],
        19: ["ASI", "Sneak Attack (10d6)"],
        20: ["Stroke of Luck (turn miss to hit or failed check to 20, 1/rest)"],
    },
    "Deathknight": {
        1: ["Dark Combat Style", "Unholy Fortitude (bonus necrotic resistance)"],
        2: ["Spellcasting", "Dark Smite (spend slot: +2d8 necrotic on melee hit)"],
        3: ["Dark Path (subclass: Blood/Unholy/Frost)", "Dark Pact (resource)"],
        4: ["ASI"],
        5: ["Extra Attack", "Aura of Dread (enemies within 10 ft: -2 to saves vs fear)"],
        6: ["Dark Path feature"],
        7: ["Soul Leech (heal 1d6 when you reduce a creature to 0 HP)"],
        8: ["ASI"],
        9: ["Death Grip (bonus action: pull target 10 ft toward you, STR save DC 14)"],
        10: ["Dark Path feature", "Aura of Dread (extends to 30 ft)"],
        11: ["Improved Dark Smite (+3d8 necrotic)"],
        12: ["ASI"],
        14: ["Dark Path feature", "Undying Will (1/long rest: drop to 1 HP instead of 0)"],
        16: ["ASI"],
        18: ["Aura improvements (all auras 30 ft)"],
        19: ["ASI"],
        20: ["Dread Lord (Dark Smite auto-applies fear on hit, no save)"],
    },
    "Sorcerer": {
        1: ["Spellcasting", "Sorcerous Origin (subclass)"],
        2: ["Font of Magic (Sorcery Points = level)"],
        3: ["Metamagic (2 options)"],
        4: ["ASI"],
        5: [],
        6: ["Origin feature"],
        7: [],
        8: ["ASI"],
        9: [],
        10: ["Metamagic (3rd option)"],
        11: [],
        12: ["ASI"],
        13: [],
        14: ["Origin feature"],
        15: [],
        16: ["ASI"],
        17: ["Metamagic (4th option)"],
        18: ["Origin feature"],
        19: ["ASI"],
        20: ["Sorcerous Restoration (regain 4 Sorcery Points on short rest)"],
    },
    "Warlock": {
        1: ["Otherworldly Patron (subclass)", "Pact Magic"],
        2: ["Eldritch Invocations (2)"],
        3: ["Pact Boon"],
        4: ["ASI"],
        5: ["Eldritch Invocations (3rd)"],
        6: ["Patron feature"],
        7: ["Eldritch Invocations (4th)"],
        8: ["ASI"],
        9: ["Eldritch Invocations (5th)"],
        10: ["Patron feature"],
        11: ["Mystic Arcanum (6th level spell)"],
        12: ["ASI", "Eldritch Invocations (6th)"],
        13: ["Mystic Arcanum (7th level spell)"],
        14: ["Patron feature"],
        15: ["Mystic Arcanum (8th level spell)", "Eldritch Invocations (7th)"],
        16: ["ASI"],
        17: ["Mystic Arcanum (9th level spell)"],
        18: ["Eldritch Invocations (8th)"],
        19: ["ASI"],
        20: ["Eldritch Master (regain all Pact Magic slots, 1 min ritual, 1/long rest)"],
    },
    "Wizard": {
        1: ["Spellcasting", "Arcane Recovery"],
        2: ["Arcane Tradition (subclass)"],
        4: ["ASI"],
        6: ["Tradition feature"],
        8: ["ASI"],
        10: ["Tradition feature"],
        12: ["ASI"],
        14: ["Tradition feature"],
        16: ["ASI"],
        18: ["Spell Mastery (cast 1st/2nd level spell at will)"],
        19: ["ASI"],
        20: ["Signature Spells (2 free 3rd-level spells per short rest)"],
    },
    "Necromancer": {
        1: ["Spellcasting", "Soul Harvest (gain 1 Soul Shard when a creature dies within 30 ft)"],
        2: ["Dark Path (subclass: Reanimator or Harvester)"],
        3: ["Undead Thrall (spend 2 Soul Shards to raise a skeleton for 1 hour)"],
        4: ["ASI"],
        5: ["Life Drain (melee spell attack, 2d8 necrotic, heal half damage dealt)"],
        6: ["Dark Path feature"],
        7: ["Soul Shield (spend 1 Shard as reaction: +3 AC until start of next turn)"],
        8: ["ASI"],
        9: ["Improved Thrall (skeleton gains +2 AC, +1d6 damage)"],
        10: ["Dark Path feature"],
        11: ["Mass Raise (spend 4 Shards: raise 3 skeletons at once)"],
        12: ["ASI"],
        14: ["Dark Path feature", "Death Ward (passive: first time reduced to 0 HP, drop to 1 instead, 1/long rest)"],
        16: ["ASI"],
        18: ["Lich's Grasp (Life Drain becomes 4d8, stuns on crit)"],
        19: ["ASI"],
        20: ["Master of Death (undead thralls are permanent until destroyed, max 5 active)"],
    },
}

ASI_LEVELS = {4, 8, 12, 16, 19}

FEATS = {
    "alert":            "Always first: +5 initiative, can't be surprised, no hidden-attacker advantage.",
    "athlete":          "+1 STR or DEX. Stand from prone costs 5 ft. Climb at full speed.",
    "actor":            "+1 CHA. Advantage on Deception/Performance when disguised. Mimic voices.",
    "charger":          "After Dash, bonus action melee attack (+5 dmg) or shove 10 ft.",
    "crossbow expert":  "Ignore loading. No disadv in melee. Bonus action hand crossbow attack.",
    "defensive duelist":"Reaction: +prof bonus to AC vs one melee attack (requires finesse weapon).",
    "dual wielder":     "+1 AC with two weapons. Two-weapon fight with non-light weapons. Draw two weapons.",
    "dungeon delver":   "ADV on Perception/Investigation for secret doors. ADV on saves vs traps. Resistance to trap damage.",
    "durable":          "+1 CON. Regain min 2×CON mod HP when spending hit dice.",
    "elemental adept":  "Spells ignore resistance to chosen damage type. Treat 1s as 2s on damage dice.",
    "grappler":         "ADV on attacks vs grappled creature. Pin: both restrained (STR check to escape).",
    "great weapon master":"−5 attack for +10 damage. Bonus action attack on crit or kill.",
    "healer":           "Stabilize with healer's kit restores 1 HP. Use kit: restore 1d6+4+HD HP (1/creature/rest).",
    "heavily armored":  "+1 STR. Proficiency with heavy armor.",
    "heavy armor master":"+1 STR. In heavy armor, reduce bludgeoning/piercing/slashing by 3.",
    "inspiring leader": "10-min speech: up to 6 allies gain temp HP = level + CHA mod.",
    "keen mind":        "+1 INT. Know N/S/E/W. Know hours to sunrise/sunset. Recall anything in past month.",
    "lightly armored":  "+1 STR or DEX. Proficiency with light armor.",
    "linguist":         "+1 INT. Learn 3 languages. Create ciphers (INT check to decode).",
    "lucky":            "3 luck points/long rest. Spend to reroll attack/ability/save or enemy attack roll.",
    "mage slayer":      "Reaction: melee attack vs nearby caster. Target disadv on concentration save. ADV on saves vs nearby casters.",
    "magic initiate":   "Learn 2 cantrips + 1 1st-level spell from chosen class.",
    "martial adept":    "Learn 2 maneuvers (d6 superiority die).",
    "medium armor master":"+1 STR or DEX. No disadv on Stealth in medium armor. DEX bonus to AC up to +3.",
    "mobile":           "+10 ft speed. Dash ignores difficult terrain. No opportunity attacks from attacked creatures.",
    "moderately armored":"+1 STR or DEX. Proficiency with medium armor and shields.",
    "mounted combatant":"ADV on melee vs unmounted smaller creatures. Redirect attacks to mount. Mount passes DEX saves.",
    "observant":        "+1 INT or WIS. Read lips. +5 passive Perception and Investigation.",
    "polearm master":   "Bonus action butt-end attack (d4). Opportunity attack when creature enters reach.",
    "resilient":        "+1 to chosen ability. Proficiency in that ability's saving throw.",
    "ritual caster":    "Ritual spellbook with 2 rituals. Add rituals found. Cast as rituals only.",
    "savage attacker":  "Once per turn, reroll weapon damage dice and use either result.",
    "sentinel":         "Opportunity attacks reduce speed to 0. Attack creatures that disengage. React to attacks on others.",
    "sharpshooter":     "No disadv at long range. Ignore half/three-quarters cover. −5 attack for +10 damage.",
    "shield master":    "Bonus action shove after Attack action. Add shield to DEX saves. No damage on successful DEX save.",
    "skilled":          "Proficiency in any 3 skills or tools.",
    "skulker":          "Hide when lightly obscured. Miss doesn't reveal position. No disadv in dim light on Perception.",
    "spell sniper":     "Double spell range. Ignore half/three-quarters cover. Learn 1 attack cantrip.",
    "tavern brawler":   "+1 STR or CON. Proficient with improvised weapons. Unarmed d4. Bonus action grapple on hit.",
    "tough":            "HP max +2 per level (retroactive).",
    "war caster":       "ADV on concentration saves. Somatic components with full hands. Opportunity attack = cast spell.",
    "weapon master":    "+1 STR or DEX. Proficiency with 4 weapons.",
}

# Classes that prepare spells (don't just know them)
SPELL_PREPARERS = {"Cleric", "Druid", "Paladin", "Wizard"}

# Multiclass spell slot table (combined caster levels)
MULTICLASS_SLOT_TABLE = {
    1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
    4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
    7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
    10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
    13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
    16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
    19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
}

# Caster level weight per class for multiclass slot calculation
CASTER_WEIGHT = {
    "Bard":1,"Cleric":1,"Druid":1,"Necromancer":1,"Sorcerer":1,"Wizard":1,
    "Paladin":0.5,"Ranger":0.5,"Deathknight":0.5,
    "Warlock":0,  # pact magic, separate
    "Barbarian":0,"Warrior":0,"Monk":0,"Rogue":0,
}

SKILL_TO_STAT = {
    "acrobatics":"dexterity","animal handling":"wisdom","arcana":"intelligence",
    "athletics":"strength","deception":"charisma","history":"intelligence",
    "insight":"wisdom","intimidation":"charisma","investigation":"intelligence",
    "medicine":"wisdom","nature":"intelligence","perception":"wisdom",
    "performance":"charisma","persuasion":"charisma","religion":"intelligence",
    "sleight of hand":"dexterity","stealth":"dexterity","survival":"wisdom",
}




# ── Helper Functions ───────────────────────────────────────────────────────────

import random
import os

def modifier(score):
    return (score - 10) // 2

def mod_str(score):
    m = modifier(score)
    return f"+{m}" if m >= 0 else str(m)

def prof_bonus(level):
    return 2 + (level - 1) // 4

def roll_ability_scores(char_class=None):
    values = []
    for _ in range(6):
        rolls = [random.randint(1, 6) for _ in range(4)]
        values.append(sum(sorted(rolls)[1:]))
    values.sort(reverse=True)
    ABILITY_SCORES_LIST = ["Strength","Dexterity","Constitution","Intelligence","Wisdom","Charisma"]
    priority = CLASS_STAT_PRIORITY.get(char_class, ABILITY_SCORES_LIST)
    scores = {}
    for stat, val in zip(priority, values):
        scores[stat] = val
    return scores

def roll_dice_str(dice_str):
    bonus = 0
    if "+" in dice_str:
        parts = dice_str.split("+")
        dice_str = parts[0]
        bonus = int(parts[1])
    count, sides = dice_str.split("d")
    rolls = [random.randint(1, int(sides)) for _ in range(int(count))]
    return rolls, sum(rolls) + bonus

def get_slots_for_level(char_class, level):
    table = CLASS_SLOT_TABLE.get(char_class, {})
    capped = min(level, max(table.keys(), default=1))
    return table.get(capped, [0]*9)

def next_level_xp(level):
    return XP_THRESHOLDS.get(level + 1, None)

def get_weapon_proficiencies(char_class, race, notes=""):
    base_profs = CLASS_WEAPON_PROF.get(char_class, set()) | RACE_WEAPON_PROF.get(race, set())
    # Check for weapon proficiency feats
    notes_lower = notes.lower() if notes else ""
    if "[feat] simple weapon proficiency" in notes_lower:
        base_profs = base_profs | SIMPLE_WEAPONS
    if "[feat] martial weapon proficiency" in notes_lower:
        base_profs = base_profs | MARTIAL_WEAPONS
    # Add campaign loot weapons if proficient with base type
    for campaign_wep, base_wep in CAMPAIGN_WEAPONS.items():
        if base_wep in base_profs:
            base_profs = base_profs | {campaign_wep}
    return base_profs

def resolve_gif(base_path, is_crit=False):
    if is_crit and base_path:
        name, ext = os.path.splitext(base_path)
        crit_path = f"{name}_crit{ext}"
        if os.path.exists(crit_path):
            return crit_path
    if base_path and os.path.exists(base_path):
        return base_path
    return None


# ── Missing Data ───────────────────────────────────────────────────────────────

EXHAUSTION_EFFECTS = {
    1: "Disadvantage on ability checks",
    2: "Speed halved",
    3: "Disadvantage on attack rolls and saving throws",
    4: "Hit point maximum halved",
    5: "Speed reduced to 0",
    6: "Death",
}

ASI_LEVELS = {4, 8, 12, 16, 19}

FEATS = {
    # Combat
    "alert": "+5 initiative, can't be surprised, no hidden-attacker advantage.",
    "great weapon master": "−5 attack for +10 damage. Bonus action attack on crit or kill.",
    "sharpshooter": "No disadv at long range. Ignore cover. −5 attack for +10 damage.",
    "sentinel": "Opportunity attacks reduce speed to 0. React to attacks on others.",
    "war caster": "ADV on concentration saves. Cast spell as opportunity attack.",
    "lucky": "3 luck points/long rest. Reroll attack/ability/save.",
    "tough": "HP max +2 per level (retroactive).",
    "resilient": "+1 to chosen ability. Proficiency in that save.",
    "mobile": "+10 ft speed. No opportunity attacks from attacked creatures.",
    "polearm master": "Bonus action butt-end attack (d4). Opportunity attack on enter reach.",
    "dual wielder": "+1 AC with two weapons. Two-weapon fight with non-light weapons. Draw two at once.",
    "shield master": "Bonus action shove after Attack. Add shield AC to DEX saves. No damage on successful DEX save.",
    "savage attacker": "Once per turn, reroll weapon damage dice and use either result.",
    "charger": "After Dash, bonus action melee attack (+5 damage) or shove 10 ft.",
    "grappler": "ADV on attacks vs grappled creature. Can pin (both restrained).",
    "defensive duelist": "Reaction: +proficiency bonus to AC vs one melee attack (requires finesse weapon).",
    "mage slayer": "Reaction: melee attack vs nearby caster. Target disadv on concentration. ADV on saves vs adjacent casters.",
    "crossbow expert": "Ignore loading. No disadv in melee. Bonus action hand crossbow attack.",
    # Skill Feats
    "intimidating presence": "+1 CHA. Proficiency in Intimidation (or expertise if already proficient).",
    "silver tongue": "+1 CHA. Proficiency in Persuasion (or expertise if already proficient).",
    "master of deception": "+1 CHA. Proficiency in Deception (or expertise if already proficient).",
    "animal handler": "+1 WIS. Proficiency in Animal Handling (or expertise). Can calm hostile beasts DC 15.",
    "naturalist": "+1 INT. Proficiency in Nature (or expertise). Identify plants/terrain automatically.",
    "medic": "+1 WIS. Proficiency in Medicine (or expertise). Stabilize as bonus action. Heal 1d6+4 with kit.",
    "investigator": "+1 INT. Proficiency in Investigation (or expertise). +5 passive Investigation.",
    "perceptive": "+1 WIS. Proficiency in Perception (or expertise). +5 passive Perception.",
    "stealthy": "+1 DEX. Proficiency in Stealth (or expertise). Can hide when lightly obscured.",
    "athlete": "+1 STR or DEX. Proficiency in Athletics (or expertise). Climb at full speed. Stand from prone costs 5 ft.",
    "performer": "+1 CHA. Proficiency in Performance (or expertise). Can distract enemies (disadv on Perception).",
    "historian": "+1 INT. Proficiency in History (or expertise). Recall lore about any location or creature.",
    "theologian": "+1 INT. Proficiency in Religion (or expertise). Identify undead/fiend weaknesses.",
    "survivalist": "+1 WIS. Proficiency in Survival (or expertise). Can't get lost. Find food/water automatically.",
    # Utility
    "dungeon delver": "ADV on Perception/Investigation for secret doors. ADV on saves vs traps. Resistance to trap damage.",
    "keen mind": "+1 INT. Know N/S/E/W. Know hours to sunrise/sunset. Recall anything from past month.",
    "linguist": "+1 INT. Learn 3 languages. Create ciphers.",
    "healer": "Stabilize with kit restores 1 HP. Use kit: heal 1d6+4+level HP (1/creature/rest).",
    "inspiring leader": "10-min speech: up to 6 allies gain temp HP = level + CHA mod.",
    "ritual caster": "Learn 2 ritual spells. Cast as rituals only (no slots).",
    "magic initiate": "Learn 2 cantrips + 1 level-1 spell from any class.",
    "skilled": "Gain proficiency in any 3 skills or tools.",
    "tavern brawler": "+1 STR or CON. Proficient with improvised weapons. Unarmed d4. Bonus action grapple on hit.",
    # Animal/Nature
    "beast whisperer": "+1 WIS. Communicate basic ideas with beasts. ADV on Animal Handling. Befriend 1 wild creature/long rest.",
    "mounted combatant": "ADV on melee vs unmounted smaller creatures. Redirect attacks to mount. Mount passes DEX saves.",
    "pack tactics": "When ally is within 5 ft of target, you have advantage on attacks against that target.",
    # Proficiency
    "light armor proficiency": "Gain proficiency with light armor.",
    "medium armor proficiency": "Gain proficiency with medium armor and shields. (Requires light armor proficiency.)",
    "heavy armor proficiency": "Gain proficiency with heavy armor. (Requires medium armor proficiency.)",
    "simple weapon proficiency": "Gain proficiency with all simple weapons (dagger, handaxe, mace, quarterstaff, spear).",
    "martial weapon proficiency": "Gain proficiency with all martial weapons (longsword, greatsword, rapier, longbow, etc.).",
}

# Items that cannot be traded
UNTRADEABLE_ITEMS = {"resurrection scroll", "blank scroll",
    "cloak of shadows", "endless quiver", "teleport stone", "whetstone of fury",
    "censer of warding", "chord of echoes", "totem of rage", "meditation beads",
    "oath sigil", "pact shard", "flux crystal", "seedling of regrowth", "runesword shard",
    "moonstone pendant", "stonebrew flask", "ember ring", "tusk of endurance",
    "adaptable satchel", "lucky coin", "tinker's lens", "diplomat's brooch", "scale of ancestry"}

# Race-specific items
RACE_ITEMS = {
    "Elf":         ("Moonstone Pendant",  "Passive — advantage on saves vs. charm."),
    "Dwarf":       ("Stonebrew Flask",    "Remove 1 exhaustion level. 1/long rest."),
    "Tiefling":    ("Ember Ring",         "Cast Hellish Rebuke as reaction (2d10 fire). 1/long rest."),
    "Half-Orc":    ("Tusk of Endurance",  "Passive — auto-succeed first death save."),
    "Human":       ("Adaptable Satchel",  "Passive — can attune to 4 items instead of 3."),
    "Halfling":    ("Lucky Coin",         "Reroll one failed save. 1/long rest."),
    "Gnome":       ("Tinker's Lens",      "Auto-succeed one Investigation check. 1/long rest."),
    "Half-Elf":    ("Diplomat's Brooch",  "Advantage on next Persuasion check. 1/short rest."),
    "Dragonborn":  ("Scale of Ancestry",  "Breath weapon deals +1d6 damage. 1/long rest."),
}

# Class-specific items
CLASS_ITEMS = {
    "Rogue":       ("Cloak of Shadows",    "stealth",      16, "Become invisible until end of next turn.", "1/short rest"),
    "Ranger":      ("Endless Quiver",      "survival",     14, "Never track ammo.", "passive"),
    "Wizard":      ("Teleport Stone",      "arcana",       16, "Party teleports to last safe room.", "1/long rest"),
    "Warrior":     ("Whetstone of Fury",   "athletics",    14, "Next attack deals +1d6 damage.", "1/short rest"),
    "Cleric":      ("Censer of Warding",   "religion",     15, "+2 AC to allies for 1 round.", "1/long rest"),
    "Bard":        ("Chord of Echoes",     "performance",  15, "Repeat last cantrip cast by ally.", "1/long rest"),
    "Barbarian":   ("Totem of Rage",       "athletics",    14, "Rage doesn't end early.", "1/long rest"),
    "Monk":        ("Meditation Beads",    "insight",      15, "Regain 2 Ki points.", "1/long rest"),
    "Necromancer": ("Bone Fetish",         "arcana",       15, "Summon skeleton for 1 combat.", "1/long rest"),
    "Paladin":     ("Oath Sigil",          "persuasion",   15, "Smite hits all enemies in 5 ft.", "1/long rest"),
    "Warlock":     ("Pact Shard",          "intimidation", 15, "Regain 1 spell slot.", "1/long rest"),
    "Sorcerer":    ("Flux Crystal",        "arcana",       16, "Next L1-2 spell free.", "1/long rest"),
    "Deathknight": ("Runesword Shard",     "intimidation", 15, "Next Dark Smite reduces target max HP.", "1/long rest"),
    "Druid":       ("Seedling of Regrowth","nature",       15, "Ally heals 1d8/turn for 3 turns.", "1/long rest"),
}

# Enemy attack stats for auto-combat
ENEMY_ATTACK_STATS = {
    "Animated Armor":       (4, "1d6", 2, "bludgeoning"),
    "Rug of Smothering":    (5, "2d6", 3, "bludgeoning"),
    "Shadow":               (4, "2d6", 2, "necrotic"),
    "The Geometry":         (2, "5d6", 0, "bludgeoning"),
    "The Echo":             (6, "1d6", 4, "bludgeoning"),
    "The Memory":           (7, "2d8", 4, "force"),
    "The Memory (Phase 2)": (7, "2d8", 4, "force"),
    "House Remnant":        (7, "2d8", 4, "bludgeoning"),
    "Minor Angle":          (4, "1d6", 2, "force"),
    "Mimic":                (5, "1d8", 3, "bludgeoning"),
}

# Multiclass spell slot table
MULTICLASS_SLOT_TABLE = {
    1:[2,0,0,0,0,0,0,0,0], 2:[3,0,0,0,0,0,0,0,0], 3:[4,2,0,0,0,0,0,0,0],
    4:[4,3,0,0,0,0,0,0,0], 5:[4,3,2,0,0,0,0,0,0], 6:[4,3,3,0,0,0,0,0,0],
    7:[4,3,3,1,0,0,0,0,0], 8:[4,3,3,2,0,0,0,0,0], 9:[4,3,3,3,1,0,0,0,0],
    10:[4,3,3,3,2,0,0,0,0],11:[4,3,3,3,2,1,0,0,0],12:[4,3,3,3,2,1,0,0,0],
    13:[4,3,3,3,2,1,1,0,0],14:[4,3,3,3,2,1,1,0,0],15:[4,3,3,3,2,1,1,1,0],
    16:[4,3,3,3,2,1,1,1,0],17:[4,3,3,3,2,1,1,1,1],18:[4,3,3,3,3,1,1,1,1],
    19:[4,3,3,3,3,2,1,1,1],20:[4,3,3,3,3,2,2,1,1],
}

CASTER_WEIGHT = {
    "Bard":1,"Cleric":1,"Druid":1,"Necromancer":1,"Sorcerer":1,"Wizard":1,
    "Paladin":0.5,"Ranger":0.5,"Deathknight":0.5,
    "Warlock":0,"Barbarian":0,"Warrior":0,"Monk":0,"Rogue":0,
}


# ── Combat Flavor Text ─────────────────────────────────────────────────────────

ENEMY_ATTACK_FLAVOR = {
    "Shadow": {
        "hit": [
            "reaches from the darkness and drains your warmth",
            "passes through your guard like smoke — but the pain is real",
            "wraps around your arm, cold seeping into bone",
            "strikes from an angle that shouldn't exist",
        ],
        "miss": [
            "passes through you like cold air — this time",
            "lunges but dissolves before making contact",
            "flickers and reforms behind you, hissing",
            "reaches for you but recoils from your light",
        ],
        "crit": [
            "engulfs you completely — for a moment, you ARE the shadow",
            "tears through you and you feel something leave — something you can't name",
        ],
    },
    "Animated Armor": {
        "hit": [
            "swings a limb that bends the wrong way — connects with a crack",
            "lurches forward, wood splintering as it strikes",
            "slams into you with the weight of something that shouldn't move",
        ],
        "miss": [
            "swings wide, joints creaking in protest",
            "lunges but collapses mid-swing, reassembling instantly",
            "strikes the ground where you stood a moment ago",
        ],
        "crit": [
            "unfolds entirely and SLAMS you with its full mass",
            "catches you off-guard — the furniture was playing dead",
        ],
    },
    "The Echo": {
        "hit": [
            "strikes with YOUR technique — but twisted, wrong",
            "hits you and whispers something only you can hear",
            "mirrors your stance perfectly before driving the blow home",
        ],
        "miss": [
            "swings exactly as you would — and you dodge exactly as you would",
            "hesitates for a fraction of a second, as if remembering something",
            "attacks your shadow instead of you",
        ],
        "crit": [
            "looks you in the eyes and says your name as the blow lands",
            "strikes with a move you haven't used yet — but were about to",
        ],
    },
    "The Memory": {
        "hit": [
            "reaches into you and pulls — something tears that isn't flesh",
            "the void touches you and for a moment you forget your own name",
            "reality bends around its fist as it connects",
            "strikes and you hear every voice it has ever consumed, screaming",
        ],
        "miss": [
            "reaches for you but you feel the house PULL you away — why?",
            "the void grazes you — close enough to feel the nothing",
            "swings through the space you occupied a heartbeat ago",
        ],
        "crit": [
            "the sphere PULSES and you are inside it for one eternal second before being thrown back",
            "grabs your face and shows you what it sees — everything, everyone, forever",
        ],
    },
    "House Remnant": {
        "hit": [
            "wraps stone and wood around your limb and SQUEEZES",
            "the walls themselves reach for you",
            "debris assembles into a fist mid-swing",
        ],
        "miss": [
            "crumbles apart before reaching you, then reforms",
            "the house tries to grab you but you're faster than stone",
        ],
        "crit": [
            "the floor opens beneath you and the house BITES",
            "engulfs your arm — you feel it trying to make you part of the wall",
        ],
    },
    "Mimic": {
        "hit": [
            "the chest UNFOLDS — a tongue of adhesive flesh lashes out and connects",
            "teeth erupt from the lid and clamp down on you",
            "a pseudopod whips from behind the 'chest' and slams into you",
        ],
        "miss": [
            "the tongue lashes out but you rip free of the adhesive",
            "teeth snap shut on empty air where you stood",
            "you dodge as the lid slams like a jaw",
        ],
        "crit": [
            "it swallows your arm up to the elbow — you feel it DIGESTING",
            "the entire chest lunges and engulfs your torso before you can react",
        ],
    },
}

# Default flavor for enemies not in the dict
DEFAULT_ATTACK_FLAVOR = {
    "hit": ["strikes true", "connects solidly", "finds its mark"],
    "miss": ["swings wide", "misses narrowly", "fails to connect"],
    "crit": ["lands a devastating blow", "strikes with terrible force"],
}

PLAYER_MISS_FLAVOR = [
    "Your strike cuts through empty air.",
    "So close — but not close enough.",
    "It shifts at the last moment.",
    "Your weapon passes through nothing.",
]

PLAYER_CRIT_FLAVOR = [
    "Time slows. The blow is perfect.",
    "You feel the impact in your bones — theirs, not yours.",
    "The house itself flinches.",
    "Something ancient and satisfied stirs in your chest.",
]


# ── Dread Flavor Text ──────────────────────────────────────────────────────────

DREAD_INCREASE_FLAVOR = {
    1: [
        "*The air feels heavier.*",
        "*Something shifts at the edge of your vision.*",
        "*You can't remember which direction you came from.*",
    ],
    2: [
        "*The walls are closer than they were a moment ago. You're sure of it.*",
        "*Your shadow moves a half-second after you do.*",
        "*The silence has a texture. It's watching.*",
    ],
    3: [
        "*You hear your own heartbeat. It's too loud. Too slow.*",
        "*The torch flickers and for one frame — one frame — the hallway was different.*",
        "*Someone is standing behind you. Don't turn around.*",
    ],
    4: [
        "*Reality blinks. When it opens its eyes again, something has changed. You can't tell what.*",
        "*Your hands don't look like your hands.*",
        "*The house knows your name. It always has.*",
    ],
    5: [
        "*You can't remember what sunlight looks like.*",
        "*The others are talking but the words are wrong. All of them.*",
        "*You are not sure you are still you.*",
    ],
    6: [
        "*The house is inside you now.*",
        "*You open your mouth to speak and hear someone else's voice.*",
    ],
}

# ── Steward Personality Lines ──────────────────────────────────────────────────

STEWARD_COMBAT_START = [
    "🕯️ *The Steward's eyes gleam.* \"Ah. It begins.\"",
    "🕯️ *A dry chuckle from the shadows.* \"Let's see how long you last.\"",
    "🕯️ *The Steward leans forward.* \"This should be... entertaining.\"",
    "🕯️ *The candle flickers.* \"Blood calls to the house. It's listening now.\"",
    "🕯️ *A whisper.* \"They were waiting for you. They're always waiting.\"",
    "🕯️ *The Steward smiles.* \"Try not to scream. It excites them.\"",
    "🕯️ *Fingers steeple in the dark.* \"I wonder... will you fight, or will you feed?\"",
]

STEWARD_COMBAT_END = [
    "🕯️ *The Steward nods slowly.* \"You survived. For now.\"",
    "🕯️ *A rasping whisper.* \"The house remembers what you did here.\"",
    "🕯️ *The Steward smiles.* \"Well done. It's watching you more closely now.\"",
    "🕯️ *A slow exhale.* \"The silence returns. But it's thinner than before.\"",
    "🕯️ *The Steward tilts his head.* \"You think that was the worst of it? How sweet.\"",
    "🕯️ *The candle steadies.* \"Catch your breath. You won't have long.\"",
]

STEWARD_TPK = [
    "🕯️ *The Steward sighs.* \"Another group. Another silence. The house is patient.\"",
    "🕯️ *A candle goes out.* \"You were warned.\"",
    "🕯️ *The Steward closes his book.* \"And so it ends. As it always does.\"",
    "🕯️ *Darkness.* \"The house thanks you for your contribution.\"",
    "🕯️ *A whisper fading.* \"You'll make fine company for the others.\"",
]

STEWARD_LEVEL_UP = [
    "🕯️ *The Steward tilts his head.* \"Stronger. Good. You'll need it.\"",
    "🕯️ *A dry laugh.* \"The house noticed that too, you know.\"",
    "🕯️ *The Steward's eyes gleam.* \"Growing. Interesting. It's watching you grow.\"",
    "🕯️ *A murmur.* \"Power attracts attention here. Be careful what you become.\"",
    "🕯️ *The candle burns brighter.* \"More fuel for the fire. Or for the house.\"",
]


# ── Enemy Spawn Gifs ───────────────────────────────────────────────────────────
ENEMY_SPAWN_GIF = {
    "Shadow": "vfx/entity_vfx/shadow_spawn.gif",
    "The Echo": "vfx/entity_vfx/echo.gif",
    "Rug of Smothering": "vfx/entity_vfx/rug.gif",
    "Banshee": "vfx/entity_vfx/banshee.gif",
    "Minor Angle": "vfx/entity_vfx/angle.gif",
    "Animated Armor": "vfx/entity_vfx/animated_armor.gif",
    "Flameskull": "vfx/entity_vfx/flameskull.gif",
    "The Hallway": "vfx/entity_vfx/hallway.gif",
    "The Lonely": "vfx/entity_vfx/lonely.gif",
    "Poltergeist": "vfx/entity_vfx/poltergeist.gif",
    "House Remnant": "vfx/entity_vfx/remnant.gif",
    "Crawling Claw": "vfx/entity_vfx/claw.gif",
    "Depth Horror": "vfx/entity_vfx/depth_horror.gif",
    "Bilge Keeper": "vfx/entity_vfx/draugr.jpg",
    "The Cook": "vfx/entity_vfx/cook.jpg",
    "The Drowned Captain": "vfx/entity_vfx/drowned_captain.jpeg",
    "Specter": "vfx/entity_vfx/spectre.gif",
    "The Memory": "vfx/entity_vfx/memory_p1_spawn.gif",
    "The Memory (Phase 2)": "vfx/entity_vfx/memory_p2_spawn.gif",
    "The Geometry": "vfx/entity_vfx/geometry.gif",
    "Mimic": "vfx/entity_vfx/mimic.gif",
}


# ── Weapon Damage Type → Gif Mapping ──────────────────────────────────────────

RANGED_WEAPONS = {"longbow", "shortbow", "crossbow, light"}

def get_weapon_gif(weapon_name):
    """Return the appropriate action gif path based on weapon's damage type."""
    if not weapon_name:
        return "vfx/action_vfx/slash.gif"  # fallback
    if weapon_name.lower() in RANGED_WEAPONS:
        return "vfx/action_vfx/arrow.gif"
    weapon_data = WEAPONS.get(weapon_name.lower())
    if not weapon_data:
        return "vfx/action_vfx/slash.gif"  # fallback
    damage_str = weapon_data[0].lower()
    if "bludgeoning" in damage_str:
        return "vfx/action_vfx/bludgeon.gif"
    elif "piercing" in damage_str:
        return "vfx/action_vfx/pierce.gif"
    else:
        return "vfx/action_vfx/slash.gif"


# ── Known Spell Limits ─────────────────────────────────────────────────────────
# Returns max non-cantrip spells a class can know at a given level.
# Cantrips are always unlimited.

def get_max_known_spells(char_class, level, int_mod=0, wis_mod=0, cha_mod=0):
    """Return max number of non-cantrip spells a class can know."""
    limits = {
        "Wizard": max(1, int_mod + level),
        "Necromancer": max(1, int_mod + level),
        "Sorcerer": 2 + level,
        "Bard": 4 + level,
        "Warlock": 2 + level,
        "Cleric": 999,  # unlimited known, limited by preparation
        "Druid": 999,
        "Paladin": max(1, cha_mod + (level // 2)),
        "Ranger": max(1, wis_mod + (level // 2)),
        "Deathknight": max(1, cha_mod + (level // 2)),
    }
    return limits.get(char_class, 0)


# ── Condition System ───────────────────────────────────────────────────────────

# Conditions that skip the afflicted entity's turn
TURN_SKIP_CONDITIONS = {"stunned", "paralyzed"}

# Conditions that apply damage at start of turn
DOT_CONDITIONS = {
    "burning": ("1d6", "fire"),
}

# Default durations for conditions (turns)
CONDITION_DEFAULTS = {
    "stunned": 1,
    "poisoned": 3,
    "frightened": 2,
    "paralyzed": 1,
    "blinded": 2,
    "restrained": 99,  # until escape
    "prone": 99,       # until stand
    "charmed": 99,     # until save or combat ends
    "burning": 3,
    "frozen": 2,
}

# Boss immunities — these conditions cannot be applied to these enemies
BOSS_CONDITION_IMMUNITIES = {
    "The Memory": {"stunned", "paralyzed", "charmed", "frightened"},
    "The Memory (Phase 2)": {"stunned", "paralyzed", "charmed", "frightened", "prone"},
    "The Echo": {"charmed", "frightened"},
    "The Geometry": {"prone", "stunned"},
    "Mimic": {"charmed"},
}

# Weapon effects that trigger on critical hit
WEAPON_ON_CRIT = {
    "soulcrusher maul": {"condition": "stunned", "duration": 1},
}

# Weapon effects that trigger on every hit
WEAPON_ON_HIT = {
    "aldric's paradox": {"effect": "displace", "save_stat": "wisdom", "save_dc": 15},
}


# ── Player Condition Resistances (faithful to D&D 5e) ──────────────────────────

# Race-based resistances (apply at all levels)
# Format: race -> {condition: "advantage"} (advantage on saves vs this condition)
RACE_CONDITION_RESISTANCE = {
    "Elf": {"charmed": "advantage", "sleep": "immune"},
    "Half-Elf": {"charmed": "advantage", "sleep": "immune"},
    "Dwarf": {"poisoned": "advantage"},
    "Halfling": {"frightened": "advantage"},
    "Gnome": {"charmed": "advantage", "frightened": "advantage"},  # vs magic specifically
    "Dragonborn": {},
    "Human": {},
    "Half-Orc": {},
    "Tiefling": {},
}

# Class-based resistances (apply at specific levels)
# Format: class -> [(min_level, {condition: "advantage"|"immune"})]
CLASS_CONDITION_RESISTANCE = {
    "Barbarian": [
        # While raging: advantage on STR saves (not directly a condition resistance)
        # Mindless Rage (lvl 6, Berserker): immune to charmed/frightened while raging
        (6, {"charmed": "immune", "frightened": "immune"}),  # Berserker subclass only
    ],
    "Monk": [
        (7, {"frightened": "immune"}),   # Stillness of Mind (end charmed/frightened on self)
        (10, {"poisoned": "immune"}),    # Purity of Body
    ],
    "Paladin": [
        (10, {"frightened": "immune"}),  # Aura of Courage
    ],
    "Ranger": [],
    "Warrior": [
        (9, {}),  # Indomitable (reroll failed save, not a condition resistance per se)
    ],
    "Cleric": [],
    "Druid": [
        (10, {"poisoned": "advantage", "charmed": "advantage"}),  # Nature's Ward (Circle of Land)
    ],
    "Bard": [],
    "Rogue": [
        (7, {}),  # Evasion (DEX saves, not condition resistance)
        (15, {"charmed": "advantage"}),  # Slippery Mind (WIS save proficiency)
    ],
    "Sorcerer": [],
    "Warlock": [],
    "Wizard": [],
    "Necromancer": [
        (14, {"frightened": "immune"}),  # Death Ward — undead affinity
    ],
    "Deathknight": [
        (1, {"frightened": "advantage"}),  # Unholy Fortitude
        (14, {"poisoned": "immune", "stunned": "advantage"}),  # Undying Will
    ],
}

def get_player_condition_resistance(char_class, race, level):
    """Return a dict of {condition: 'advantage'|'immune'} for a player based on class, race, level."""
    resistances = {}
    # Race resistances (always active)
    race_res = RACE_CONDITION_RESISTANCE.get(race, {})
    resistances.update(race_res)
    # Class resistances (level-gated)
    class_res = CLASS_CONDITION_RESISTANCE.get(char_class, [])
    for min_level, cond_dict in class_res:
        if level >= min_level:
            for cond, res_type in cond_dict.items():
                # Immune overrides advantage
                if res_type == "immune" or resistances.get(cond) != "immune":
                    resistances[cond] = res_type
    return resistances


# ── Enemy Condition Application (to players on hit) ────────────────────────────
# Format: enemy_name -> {condition, duration, save_stat, save_dc, chance}
# chance: 1.0 = always on hit, 0.5 = 50% chance, etc.

ENEMY_ON_HIT_CONDITION = {
    "The Echo": {"condition": "frightened", "duration": 1, "save_stat": "wisdom", "save_dc": 14, "chance": 0.5},
    "The Memory": {"condition": "frightened", "duration": 1, "save_stat": "wisdom", "save_dc": 15, "chance": 0.3},
    "The Memory (Phase 2)": {"condition": "frightened", "duration": 2, "save_stat": "wisdom", "save_dc": 15, "chance": 0.4},
    "Mimic": {"condition": "restrained", "duration": 2, "save_stat": "strength", "save_dc": 13, "chance": 0.5},
    "The Geometry": {"condition": "prone", "duration": 1, "save_stat": "dexterity", "save_dc": 13, "chance": 0.4},
    "Bilge Keeper": {"condition": "restrained", "duration": 2, "save_stat": "constitution", "save_dc": 13, "chance": 0.3},
    "The Cook": {"condition": "poisoned", "duration": 2, "save_stat": "constitution", "save_dc": 12, "chance": 0.2},
    "The Drowned Captain": [
        {"condition": "prone", "duration": 1, "save_stat": "strength", "save_dc": 13, "chance": 0.4},
        {"condition": "frightened", "duration": 1, "save_stat": "wisdom", "save_dc": 14, "chance": 0.2},
    ],
    "Depth Horror": [
        {"condition": "frightened", "duration": 2, "save_stat": "wisdom", "save_dc": 15, "chance": 0.5},
        {"condition": "restrained", "duration": 1, "save_stat": "strength", "save_dc": 15, "chance": 0.3},
    ],
    "Slappy": [
        {"condition": "weak venom", "duration": 3, "save_stat": "constitution", "save_dc": 10, "chance": 0.5},
        {"condition": "stunned", "duration": 1, "save_stat": "constitution", "save_dc": 12, "chance": 0.2},
    ],
}


# ── Steward Personality Lines (for various bot responses) ──────────────────────

STEWARD_POTION = [
    "🕯️ *The Steward watches you drink.* \"Savor it. There won't always be another.\"",
    "🕯️ *A dry nod.* \"Smart. The dead can't drink potions.\"",
    "🕯️ *The Steward's lip curls.* \"Desperation tastes sweet, doesn't it?\"",
    "🕯️ *A murmur.* \"The house provides. But the house always collects.\"",
    "🕯️ *The candle flickers.* \"Healing here is... temporary. Everything is temporary here.\"",
    "🕯️ *The Steward watches.* \"Drink. But know that every sip is borrowed time.\"",
]

STEWARD_DEATH = [
    "🕯️ *The Steward sighs.* \"Another one falls. The house is patient.\"",
    "🕯️ *A whisper.* \"Not yet. Not yet. But soon.\"",
    "🕯️ *The candle flickers.* \"The house remembers your face now.\"",
    "🕯️ *Silence.* \"...one less heartbeat. The walls noticed.\"",
    "🕯️ *The Steward kneels.* \"The floor is warm where they fell. It's feeding.\"",
    "🕯️ *A cold breath.* \"They're not gone. Nothing leaves this house.\"",
]

STEWARD_RESURRECT = [
    "🕯️ *The Steward raises an eyebrow.* \"Cheating death? The house doesn't forget debts.\"",
    "🕯️ *A rasping laugh.* \"Back from the edge. But the edge remembers you.\"",
    "🕯️ *The candle flares.* \"Pulled back. But something followed them. Something always follows.\"",
    "🕯️ *The Steward frowns.* \"The dead don't like being disturbed. Neither does the house.\"",
    "🕯️ *A whisper.* \"You owe the darkness a life now. It will collect.\"",
]

STEWARD_LOOT = [
    "🕯️ *The Steward gestures.* \"Take what the dead no longer need.\"",
    "🕯️ *A whisper.* \"Everything in this house has a price. You just haven't paid yet.\"",
    "🕯️ *The Steward smiles thinly.* \"Gifts from the house. How generous. How unlike it.\"",
    "🕯️ *A murmur.* \"The previous owners won't miss these. They don't miss anything anymore.\"",
    "🕯️ *The candle dims.* \"Take it. But remember — the house gave it to you. It can take it back.\"",
]

STEWARD_REST = [
    "🕯️ *The Steward leans against the wall.* \"Rest. But don't close your eyes for too long.\"",
    "🕯️ *A murmur.* \"The house doesn't sleep. Remember that.\"",
    "🕯️ *The candle dims.* \"Quiet now. Quiet.\"",
    "🕯️ *The Steward watches.* \"Sleep if you must. But the walls are thinner when you dream.\"",
    "🕯️ *A whisper.* \"The last group rested here too. Right here. In this exact spot.\"",
    "🕯️ *The Steward's voice drops.* \"Listen. Do you hear it? The house breathing? No? ...Good.\"",
    "🕯️ *Silence stretches.* \"...the quiet is louder here than it should be.\"",
]

STEWARD_DODGE_TIMEOUT = [
    "🕯️ *The Steward tuts.* \"Hesitation is a choice. The house rewards decisiveness.\"",
    "🕯️ *A cold stare.* \"Frozen. Like the others before you.\"",
    "🕯️ *The Steward shakes his head.* \"The house feeds on indecision. You just gave it a meal.\"",
    "🕯️ *A whisper.* \"Time moves differently here. But it still moves. And you didn't.\"",
    "🕯️ *The candle flickers.* \"Paralyzed by choice? Or by something else?\"",
]

STEWARD_CHAR_CREATED = [
    "🕯️ *The Steward inspects you.* \"Another soul enters the ledger. Welcome.\"",
    "🕯️ *A thin smile.* \"Fresh. Unbroken. We'll see how long that lasts.\"",
    "🕯️ *The Steward writes something in his book.* \"Name noted. Face remembered. You may proceed.\"",
    "🕯️ *A dry laugh.* \"They all look so hopeful at the beginning.\"",
    "🕯️ *The candle flares.* \"The house has a new guest. It's... excited.\"",
]


# ── Racial Abilities System ────────────────────────────────────────────────────

DRAGONBORN_ANCESTRY = {
    "Black":  {"damage_type": "acid",      "save_stat": "dexterity"},
    "Blue":   {"damage_type": "lightning", "save_stat": "dexterity"},
    "Brass":  {"damage_type": "fire",      "save_stat": "dexterity"},
    "Bronze": {"damage_type": "lightning", "save_stat": "dexterity"},
    "Copper": {"damage_type": "acid",      "save_stat": "dexterity"},
    "Gold":   {"damage_type": "fire",      "save_stat": "dexterity"},
    "Green":  {"damage_type": "poison",    "save_stat": "constitution"},
    "Red":    {"damage_type": "fire",      "save_stat": "dexterity"},
    "Silver": {"damage_type": "cold",      "save_stat": "constitution"},
    "White":  {"damage_type": "cold",      "save_stat": "constitution"},
}

RACIAL_ABILITIES = {
    "Dragonborn": {
        "name": "Dragonborn Breath",
        "description": "Exhale destructive energy. All enemies make a save or take damage.",
        "type": "damage_aoe",
        "damage": "2d6",
        "scaling": {6: "3d6", 11: "4d6", 16: "5d6"},
        "damage_type": "fire",
        "save_stat": "dexterity",
        "save_dc": "8+CON+prof",
        "uses": 1,
        "recharge": "short_rest",
    },
    "Half-Orc": {
        "name": "Relentless Endurance",
        "description": "Drop to 1 HP instead of 0, once per long rest.",
        "type": "passive_trigger",
        "uses": 1,
        "recharge": "long_rest",
    },
    "Halfling": {
        "name": "Lucky",
        "description": "Reroll a natural 1 on any d20 roll.",
        "type": "passive_trigger",
        "uses": -1,
        "recharge": "none",
    },
    "Tiefling": {
        "name": "Hellish Rebuke",
        "description": "When hit, deal 3d10 fire to attacker. Once per long rest.",
        "type": "damage_single",
        "damage": "3d10",
        "scaling": {5: "4d10"},
        "damage_type": "fire",
        "save_stat": "dexterity",
        "save_dc": "8+CHA+prof",
        "uses": 1,
        "recharge": "long_rest",
    },
    "Elf": {
        "name": "Trance",
        "description": "4 hours of meditation replaces 8 hours of sleep.",
        "type": "passive",
        "uses": -1,
        "recharge": "none",
    },
    "Half-Elf": {
        "name": "Fey Ancestry",
        "description": "Advantage on saves vs charmed. Immune to magical sleep.",
        "type": "passive",
        "uses": -1,
        "recharge": "none",
    },
    "Dwarf": {
        "name": "Dwarven Resilience",
        "description": "Advantage on saves vs poison. Resistance to poison damage.",
        "type": "passive",
        "uses": -1,
        "recharge": "none",
    },
    "Gnome": {
        "name": "Gnome Cunning",
        "description": "Advantage on INT/WIS/CHA saves vs magic.",
        "type": "passive",
        "uses": -1,
        "recharge": "none",
    },
    "Human": {
        "name": "Determination",
        "description": "Reroll one failed ability check. Once per long rest.",
        "type": "reroll",
        "uses": 1,
        "recharge": "long_rest",
    },
}

def get_breath_damage(level):
    if level >= 16: return "5d6"
    if level >= 11: return "4d6"
    if level >= 6: return "3d6"
    return "2d6"


def halfling_lucky(roll, race):
    """Reroll a nat 1 if the character is a Halfling. Returns (final_roll, was_rerolled)."""
    if roll == 1 and race == "Halfling":
        import random as _r
        return _r.randint(1, 20), True
    return roll, False


# ── Item Emojis ────────────────────────────────────────────────────────────────

ITEM_EMOJI = {
    # Base weapons
    "dagger": "🗡️", "shortsword": "⚔️", "longsword": "⚔️", "greatsword": "⚔️",
    "rapier": "🤺", "handaxe": "🪓", "greataxe": "🪓", "spear": "🔱",
    "quarterstaff": "🏑", "mace": "🔨", "flail": "🔨", "morningstar": "🔨",
    "warhammer": "🔨", "shortbow": "🏹", "longbow": "🏹", "crossbow, light": "🏹",
    # Campaign weapons
    "splinterfang hatchet": "🪓", "angle's edge": "🔷", "longsword of the remnant": "⚔️",
    "mirrorbane rapier": "🪞", "voidcleaver greatsword": "🌀", "hollowshot longbow": "🌑",
    "soulcrusher maul": "💀", "aldric's paradox": "✨", "fractal wand": "🔮",
    "copycat shortbow": "🎭", "echo staff": "🎭", "mindbreak staff": "🧠",
    "hungering blade": "🩸", "tome of unmaking": "📕",
    # Base armor
    "padded": "🧥", "leather": "🧥", "studded leather": "🧥",
    "hide": "🦺", "chain shirt": "⛓️", "scale mail": "🐉", "breastplate": "🦺",
    "half plate": "🦾", "ring mail": "⛓️", "chain mail": "⛓️",
    "splint": "🦾", "plate": "🦾", "shield": "🛡️",
    # Campaign armor
    "geometrist's hide": "🔷", "echoweave leather": "🪞", "folded chain shirt": "⛓️",
    "reflective chain": "⛓️", "voidtouched breastplate": "🌀", "voidweave robes": "🌀",
    "abyssal plate": "🦾", "hollowhide leather": "🌑", "hollowplate": "🦾",
    # Consumables & loot
    "health potion": "❤️", "everlight torch": "🔦", "bandage": "🩹",
    "antidote vial": "🧪", "smoke bomb": "💨", "whetstone": "🪨",
    "soul fragment": "👻", "tincture of clarity": "💎", "essence of forgotten breath": "💨",
    "heart of the house": "🫀", "resurrection scroll": "📜", "arcane focus": "🔮",
    "scholar's pack": "📚", "diplomat's brooch": "📌",
}

def get_item_emoji(item_name):
    """Return the emoji for an item, or a default based on type."""
    return ITEM_EMOJI.get(item_name.lower().strip(), "•")


# ── Item Database (descriptions, types, effects) ──────────────────────────────

ITEM_DATABASE = {
    # Consumables
    "health potion": {"type": "consumable", "rarity": "Common", "description": "A vial of red liquid that shimmers when agitated.", "effect": "Heal 2d4+2 HP.", "useable": True, "equippable": False},
    "bandage": {"type": "consumable", "rarity": "Common", "description": "Clean linen strips. No magic required.", "effect": "Heal 1d4 HP.", "useable": True, "equippable": False},
    "antidote vial": {"type": "consumable", "rarity": "Common", "description": "A murky green liquid that smells of mint and bile.", "effect": "Remove poisoned condition.", "useable": True, "equippable": False},
    "resurrection scroll": {"type": "consumable", "rarity": "Rare", "description": "Ancient parchment inscribed with golden runes. Burns after use.", "effect": "Revive a downed ally to 1 HP.", "useable": True, "equippable": False},
    "smoke bomb": {"type": "consumable", "rarity": "Uncommon", "description": "A small clay sphere filled with alchemical powder.", "effect": "Disengage without provoking opportunity attacks.", "useable": True, "equippable": False},
    "tincture of clarity": {"type": "consumable", "rarity": "Rare", "description": "Crystal-clear liquid in a glass vial. Tastes like cold air.", "effect": "Remove frightened/charmed. Advantage on next WIS save.", "useable": True, "equippable": False},
    "essence of forgotten breath": {"type": "consumable", "rarity": "Very Rare", "description": "A sealed vial containing nothing visible — but when opened, you inhale something ancient.", "effect": "Restore all spell slots.", "useable": True, "equippable": False},
    "vial of spatial mending": {"type": "consumable", "rarity": "Uncommon", "description": "The liquid inside seems to occupy more space than the vial allows.", "effect": "Heal 3d8 HP. Remove restrained/prone.", "useable": True, "equippable": False},
    "heart of the house": {"type": "consumable", "rarity": "Very Rare", "description": "A pulsing, warm stone that beats like a heart. It shouldn't exist.", "effect": "Gain 20 temp HP. Immune to frightened for 1 hour.", "useable": True, "equippable": False},
    "soul fragment": {"type": "consumable", "rarity": "Rare", "description": "A translucent shard that whispers when held. Someone's last thought.", "effect": "+1d6 to next attack roll or saving throw.", "useable": True, "equippable": False},
    "whetstone": {"type": "consumable", "rarity": "Common", "description": "A flat stone worn smooth by use. Smells of iron.", "effect": "Next weapon attack deals +2 damage.", "useable": True, "equippable": False},
    # Passive gear
    "everlight torch": {"type": "gear", "rarity": "Uncommon", "description": "A torch that never extinguishes. The flame is cold to the touch.", "effect": "Never goes out. Advantage on Perception in darkness.", "useable": False, "equippable": False},
    "arcane focus": {"type": "gear", "rarity": "Common", "description": "A crystal orb, wand, or staff used to channel arcane energy.", "effect": "Required for spellcasting. No mechanical bonus.", "useable": False, "equippable": False},
    "scholar's pack": {"type": "gear", "rarity": "Common", "description": "Contains ink, quill, parchment, a book, and a small knife.", "effect": "Flavor item. Useful for notes and research.", "useable": False, "equippable": False},
    "diplomat's brooch": {"type": "gear", "rarity": "Uncommon", "description": "A silver pin shaped like two clasped hands. Warm to the touch.", "effect": "Advantage on Persuasion checks.", "useable": False, "equippable": False},
    # Campaign weapons
    "splinterfang hatchet": {"type": "weapon", "rarity": "Uncommon", "description": "A jagged hatchet made from a creature's fang. Splits on impact.", "effect": "+1 damage to prone targets.", "useable": False, "equippable": True},
    "angle's edge": {"type": "weapon", "rarity": "Uncommon", "description": "A blade that bends light around it. The edge is never where it appears.", "effect": "On hit: target's next attack has disadvantage (1/short rest).", "useable": False, "equippable": True},
    "longsword of the remnant": {"type": "weapon", "rarity": "Uncommon", "description": "A blade carried by those who came before. It remembers them.", "effect": "Glows within 30 ft of undead.", "useable": False, "equippable": True},
    "mirrorbane rapier": {"type": "weapon", "rarity": "Rare", "description": "A rapier that reflects no light. Shapechangers recoil from it.", "effect": "+1d4 damage vs shapechangers and illusions.", "useable": False, "equippable": True},
    "fractal wand": {"type": "weapon", "rarity": "Uncommon", "description": "A wand that splits into smaller copies of itself at the tip.", "effect": "Spell attacks deal +1 damage.", "useable": False, "equippable": True},
    "copycat shortbow": {"type": "weapon", "rarity": "Rare", "description": "A bow that hums the last sound it heard before firing.", "effect": "On crit: copy target's last action (DM adjudicates).", "useable": False, "equippable": True},
    "echo staff": {"type": "weapon", "rarity": "Rare", "description": "A staff that repeats your words a half-second late. The echo is louder.", "effect": "Spell save DC +1.", "useable": False, "equippable": True},
    "voidcleaver greatsword": {"type": "weapon", "rarity": "Very Rare", "description": "A greatsword forged from nothing. The blade is an absence of light.", "effect": "On kill: gain 5 temp HP.", "useable": False, "equippable": True},
    "hollowshot longbow": {"type": "weapon", "rarity": "Very Rare", "description": "Arrows fired from this bow pass through solid matter.", "effect": "Ignore half and three-quarter cover.", "useable": False, "equippable": True},
    "soulcrusher maul": {"type": "weapon", "rarity": "Very Rare", "description": "A massive hammer that hums with trapped screams.", "effect": "On crit: target stunned 1 turn.", "useable": False, "equippable": True},
    "mindbreak staff": {"type": "weapon", "rarity": "Very Rare", "description": "A staff of black glass. Looking at it too long gives you a nosebleed.", "effect": "Spell attacks +2 damage. On crit: target confused 1 turn.", "useable": False, "equippable": True},
    "hungering blade": {"type": "weapon", "rarity": "Very Rare", "description": "A longsword that drinks. The fuller is always wet.", "effect": "On kill: heal 1d8 HP.", "useable": False, "equippable": True},
    "tome of unmaking": {"type": "weapon", "rarity": "Very Rare", "description": "A book bound in skin that isn't leather. Pages fill themselves.", "effect": "+1 spell save DC. Once/long rest: force one enemy to auto-fail a save.", "useable": False, "equippable": True},
    "tidecaller axe": {"type": "weapon", "rarity": "Uncommon", "description": "A handaxe of blue-black iron. Frost forms on the blade in salt air.", "effect": "+1d4 cold damage.", "useable": False, "equippable": True},
    "coral blade": {"type": "weapon", "rarity": "Rare", "description": "A longsword grown from black coral. Seawater drips from it endlessly.", "effect": "+1d6 cold damage. On crit: target's speed halved for 1 turn.", "useable": False, "equippable": True},
    "harpoon of the deep": {"type": "weapon", "rarity": "Rare", "description": "A rusted harpoon that pulls toward living things.", "effect": "On hit: STR DC 13 or pulled 10 ft toward you.", "useable": False, "equippable": True},
    "stormbreaker maul": {"type": "weapon", "rarity": "Very Rare", "description": "A warhammer crackling with purple lightning. Thunder follows each swing.", "effect": "+1d6 lightning damage. On crit: all creatures within 5 ft take 1d8 thunder.", "useable": False, "equippable": True},
    "krakens tooth": {"type": "weapon", "rarity": "Very Rare", "description": "A dagger carved from a tooth the size of a man. It vibrates near water.", "effect": "+2d4 cold damage. On kill: gain 10 temp HP.", "useable": False, "equippable": True},
    "sigrids resolve": {"type": "weapon", "rarity": "Legendary", "description": "A longsword that burns with cold fire. Sigrid carried this before the ship took her legs. It remembers her fury.", "effect": "+2d6 radiant damage vs undead/aberrations. Immune to frightened while wielding. Once/long rest: auto-succeed one STR save.", "useable": False, "equippable": True},
    "barnacle mail": {"type": "armor", "rarity": "Uncommon", "description": "Chain mail encrusted with living barnacles. They tighten protectively when struck.", "effect": "AC 16. Resistance to cold damage.", "useable": False, "equippable": True},
    "drowned leather": {"type": "armor", "rarity": "Rare", "description": "Leather armor that's perpetually damp. Water slides off you.", "effect": "AC 12 + DEX. Advantage on saves vs being pushed/pulled. +5 to swim checks.", "useable": False, "equippable": True},
    "kelpweave robes": {"type": "armor", "rarity": "Rare", "description": "Robes woven from deep-sea kelp. They move on their own in still air.", "effect": "AC 11 + DEX. +1 spell save DC. Resistance to cold damage.", "useable": False, "equippable": True},
    "coral plate": {"type": "armor", "rarity": "Very Rare", "description": "Splint armor grown from living coral. It repairs itself in saltwater.", "effect": "AC 17. Resistance to cold. Regenerate 1 HP/turn while in rain or water.", "useable": False, "equippable": True},
    "sword of testing": {"type": "weapon", "rarity": "Rare", "description": "A blade that exists only for testing purposes. It hums with QA energy.", "effect": "+1 to hit. Glows when bugs are near.", "useable": False, "equippable": True},
    "shield of debugging": {"type": "armor", "rarity": "Rare", "description": "A shield covered in error logs. Surprisingly protective.", "effect": "+2 AC. Reflects bad code.", "useable": False, "equippable": True},
    "helmet of feedback": {"type": "armor", "rarity": "Uncommon", "description": "A helmet that whispers suggestions for improvement.", "effect": "+1 AC. Advantage on Investigation checks.", "useable": False, "equippable": True},
    "potion of qa": {"type": "consumable", "rarity": "Uncommon", "description": "A bubbling purple liquid labeled 'DRINK ME (for testing)'.", "effect": "Heal 4d4+4 HP. Tastes like validation.", "useable": True, "equippable": False},
    "aldric's paradox": {"type": "weapon", "rarity": "Legendary", "description": "A weapon that exists in two states simultaneously. It was never forged — it was *remembered*.", "effect": "See !voidwalk. Legendary weapon with unique properties.", "useable": False, "equippable": True},
    # Campaign armor
    "geometrist's hide": {"type": "armor", "rarity": "Uncommon", "description": "Hide armor covered in impossible angles. The stitching moves.", "effect": "+1 AC vs ranged attacks.", "useable": False, "equippable": True},
    "echoweave leather": {"type": "armor", "rarity": "Rare", "description": "Leather that absorbs sound. Your footsteps vanish.", "effect": "Advantage on Stealth. First attack against you each combat has disadvantage.", "useable": False, "equippable": True},
    "folded chain shirt": {"type": "armor", "rarity": "Uncommon", "description": "Chain mail folded into an impossibly small square. Unfolds instantly.", "effect": "Can be donned as a bonus action.", "useable": False, "equippable": True},
    "reflective chain": {"type": "armor", "rarity": "Rare", "description": "Chain links that mirror everything. Attackers see themselves die.", "effect": "Reflect 1d4 damage back to melee attackers.", "useable": False, "equippable": True},
    "voidtouched breastplate": {"type": "armor", "rarity": "Very Rare", "description": "A breastplate with a hole where the heart should be. The hole goes deeper than the metal.", "effect": "Resistance to necrotic damage.", "useable": False, "equippable": True},
    "voidweave robes": {"type": "armor", "rarity": "Very Rare", "description": "Robes woven from darkness. They billow without wind.", "effect": "+1 spell save DC. Resistance to psychic damage.", "useable": False, "equippable": True},
    "abyssal plate": {"type": "armor", "rarity": "Very Rare", "description": "Plate armor pulled from the void. It's heavier than it should be.", "effect": "Resistance to necrotic. Immune to frightened.", "useable": False, "equippable": True},
    "hollowhide leather": {"type": "armor", "rarity": "Very Rare", "description": "Leather that came from something that was never alive.", "effect": "Advantage on saves vs magic. +1 AC in darkness.", "useable": False, "equippable": True},
    "hollowplate": {"type": "armor", "rarity": "Very Rare", "description": "Half plate forged inside the house. It remembers being worn by someone else.", "effect": "Resistance to necrotic + psychic. -10 ft speed.", "useable": False, "equippable": True},
}

def get_item_info(item_name):
    """Look up an item in the database. Returns dict or None."""
    return ITEM_DATABASE.get(item_name.lower().strip())


# ── Buff/Debuff System ─────────────────────────────────────────────────────────

# Debuff effects: condition -> {attack_mod, save_mod, check_mod, ac_mod, speed_mod, special}
CONDITION_EFFECTS = {
    "poisoned":      {"attack_mod": -99, "check_mod": -99, "special": "disadvantage_attacks_checks"},
    "frightened":    {"attack_mod": -99, "check_mod": -99, "special": "disadvantage_attacks_checks"},
    "charmed":       {"special": "cant_attack_charmer"},
    "blinded":       {"attack_mod": -99, "special": "disadvantage_attacks; advantage_against"},
    "deafened":      {"special": "auto_fail_hearing"},
    "stunned":       {"special": "cant_act; advantage_against; auto_fail_str_dex"},
    "paralyzed":     {"special": "cant_act; advantage_against; auto_fail_str_dex; auto_crit_melee"},
    "restrained":    {"attack_mod": -99, "special": "disadvantage_attacks_dex; advantage_against; speed_0"},
    "prone":         {"attack_mod": -99, "special": "disadvantage_attacks; advantage_melee_against; disadvantage_ranged_against"},
    "incapacitated": {"special": "cant_act"},
}

# Poisons: name -> {condition, dot_damage, dot_type, duration, extra}
POISONS = {
    "weak venom":        {"condition": "poisoned", "dot": "1d4", "dot_type": "poison", "duration": 3, "extra": None},
    "creeping rot":      {"condition": None, "dot": "1d6", "dot_type": "necrotic", "duration": 3, "extra": "con_save_minus_2"},
    "mindnumb toxin":    {"condition": "poisoned", "dot": None, "dot_type": None, "duration": 2, "extra": "cant_cast"},
    "blackhollow spores":{"condition": "poisoned", "dot": None, "dot_type": None, "duration": -1, "extra": "wis_save_disadvantage"},
}

# Curses: name -> {effect_desc, mechanical, cure}
CURSES = {
    "curse of frailty":  {"desc": "Max HP reduced by 10.", "mechanical": "max_hp_minus_10", "cure": "Remove Curse spell or quest"},
    "curse of silence":  {"desc": "Can't cast verbal spells.", "mechanical": "no_verbal_spells", "cure": "Remove Curse or long rest"},
    "curse of the house": {"desc": "+1 Dread per long rest.", "mechanical": "dread_per_rest", "cure": "Story event only"},
    "curse of echoes":   {"desc": "Attacks against you have +2 to hit.", "mechanical": "ac_minus_2", "cure": "Remove Curse"},
}

# Diseases: name -> {effect_desc, mechanical, cure}
DISEASES = {
    "void sickness":    {"desc": "-1 to all saves. Can't benefit from short rest.", "mechanical": "saves_minus_1; no_short_rest", "cure": "3 long rests or Greater Restoration"},
    "creeping madness": {"desc": "Disadvantage on INT/WIS checks. Random whispers.", "mechanical": "disadvantage_int_wis", "cure": "Greater Restoration"},
    "hollowing":        {"desc": "Lose 1 max HP per hour in the house.", "mechanical": "max_hp_drain", "cure": "Leave the house or Heart of the House"},
}

# Buffs: name -> {effect_desc, mechanical, duration_turns}
BUFFS = {
    # Stat buffs
    "strength":    {"desc": "+2 to STR checks and melee damage.", "mechanical": "str_plus_2", "duration": -1},
    "constitution":{"desc": "+2 to CON saves and +5 temp HP.", "mechanical": "con_plus_2; temp_hp_5", "duration": -1},
    "intellect":   {"desc": "+2 to INT checks and spell damage.", "mechanical": "int_plus_2", "duration": -1},
    "dexterity":   {"desc": "+2 to DEX saves and AC.", "mechanical": "dex_plus_2; ac_plus_2", "duration": -1},
    "wisdom":      {"desc": "+2 to WIS saves and Perception.", "mechanical": "wis_plus_2", "duration": -1},
    "charisma":    {"desc": "+2 to CHA checks and spell save DC.", "mechanical": "cha_plus_2", "duration": -1},
    # Combat buffs
    "blessed":     {"desc": "+1d4 to attacks and saves.", "mechanical": "attacks_plus_1d4; saves_plus_1d4", "duration": 3},
    "haste":       {"desc": "Extra action per turn. +2 AC.", "mechanical": "extra_action; ac_plus_2", "duration": 3},
    "shielded":    {"desc": "+2 AC.", "mechanical": "ac_plus_2", "duration": -1},
    "inspired":    {"desc": "Advantage on next roll.", "mechanical": "advantage_next", "duration": 1},
    "raging":      {"desc": "Resistance to physical damage. +2 melee damage.", "mechanical": "resist_physical; melee_plus_2", "duration": -1},
}

# All afflictions combined for lookup
ALL_AFFLICTIONS = {}
ALL_AFFLICTIONS.update({k: {"category": "condition", **v} for k, v in CONDITION_EFFECTS.items()})
ALL_AFFLICTIONS.update({k: {"category": "poison", **v} for k, v in POISONS.items()})
ALL_AFFLICTIONS.update({k: {"category": "curse", **v} for k, v in CURSES.items()})
ALL_AFFLICTIONS.update({k: {"category": "disease", **v} for k, v in DISEASES.items()})
ALL_AFFLICTIONS.update({k: {"category": "buff", **v} for k, v in BUFFS.items()})


# ── Spell Effects (auto-applied on cast) ──────────────────────────────────────
# type: "self_buff" applies to caster, "enemy_debuff" applies to target, "ally_buff" applies to target ally
SPELL_ON_CAST_EFFECT = {
    "shield":       {"type": "self_buff", "buff": "shielded", "desc": "+5 AC until next turn", "ac_bonus": 5, "duration": 1},
    "hex":          {"type": "enemy_debuff", "condition": "hexed", "desc": "+1d6 necrotic on each hit vs target"},
    "hunter's mark": {"type": "enemy_debuff", "condition": "marked", "desc": "+1d6 damage on each hit vs target"},
    "faerie fire":  {"type": "enemy_debuff", "condition": "faerie_fire", "desc": "Attacks vs target have advantage"},
    "entangle":     {"type": "enemy_debuff", "condition": "restrained", "desc": "Target restrained. STR DC to break."},
    "divine smite": {"type": "self_buff", "buff": "smiting", "desc": "+2d8 radiant on next hit", "duration": 1},
    "bless":        {"type": "self_buff", "buff": "blessed", "desc": "+1d4 to attacks and saves", "duration": 3},
    "haste":        {"type": "self_buff", "buff": "haste", "desc": "+2 AC, extra action", "ac_bonus": 2, "duration": 3},
    "mirror image":  {"type": "self_buff", "buff": "mirror_image", "desc": "3 duplicates. Attacks may hit a duplicate instead.", "duration": -1},
    "fire shield":  {"type": "self_buff", "buff": "fire_shield", "desc": "Resistance to cold/fire. Melee attackers take 2d8 fire.", "duration": -1},
    "death ward":   {"type": "self_buff", "buff": "death_ward", "desc": "First time you drop to 0 HP, drop to 1 instead.", "duration": -1},
}


# ── Weapon/Armor Passive Effects (auto-applied in combat) ──────────────────────

# Extra damage dice added to every hit with this weapon
WEAPON_BONUS_DAMAGE = {
    "tidecaller axe": "1d4",
    "coral blade": "1d6",
    "stormbreaker maul": "1d6",
    "krakens tooth": "2d4",
    "sigrids resolve": "2d6",  # vs undead/aberrations only (checked in code)
    "mirrorbane rapier": "1d4",  # vs shapechangers/illusions
    "fractal wand": "1",  # flat +1
    "mindbreak staff": "2",  # flat +2
}

# Damage type for bonus damage (defaults to weapon's base type if not specified)
WEAPON_BONUS_TYPE = {
    "tidecaller axe": "cold",
    "coral blade": "cold",
    "stormbreaker maul": "lightning",
    "krakens tooth": "cold",
    "sigrids resolve": "radiant",
    "mirrorbane rapier": "force",
}

# Effect when you kill an enemy with this weapon
WEAPON_ON_KILL = {
    "voidcleaver greatsword": {"effect": "temp_hp", "value": 5},
    "hungering blade": {"effect": "heal", "value": "1d8"},
    "krakens tooth": {"effect": "temp_hp", "value": 10},
}

# Passive armor effects (applied while equipped)
ARMOR_PASSIVE = {
    "barnacle mail": {"resistance": ["cold"]},
    "drowned leather": {"advantage_vs": ["pushed", "pulled"], "swim_bonus": 5},
    "kelpweave robes": {"spell_dc_bonus": 1, "resistance": ["cold"]},
    "coral plate": {"resistance": ["cold"], "regen_in_water": 1},
    "voidtouched breastplate": {"resistance": ["necrotic"]},
    "voidweave robes": {"spell_dc_bonus": 1, "resistance": ["psychic"]},
    "abyssal plate": {"resistance": ["necrotic"], "immune": ["frightened"]},
    "hollowhide leather": {"advantage_vs_magic_saves": True, "ac_bonus_darkness": 1},
    "hollowplate": {"resistance": ["necrotic", "psychic"], "speed_penalty": 10},
    "echoweave leather": {"advantage": ["stealth"], "first_attack_disadvantage": True},
    "reflective chain": {"reflect_damage": "1d4"},
    "geometrist's hide": {"ac_bonus_vs_ranged": 1},
}


# ── Race Character Art (shown on !char embed) ─────────────────────────────────

RACE_VFX = {
    "Human": "vfx/character_vfx/human.jpg",
    "Elf": "vfx/character_vfx/elf.gif",
    "Dwarf": "vfx/character_vfx/dwarf.gif",
    "Halfling": "vfx/character_vfx/halfling.gif",
    "Dragonborn": "vfx/character_vfx/dragonborn.gif",
    "Gnome": "vfx/character_vfx/gnome.gif",
    "Half-Elf": "vfx/character_vfx/half_elf.gif",
    "Half-Orc": "vfx/character_vfx/half_orc.jpeg",
    "Tiefling": "vfx/character_vfx/tiefling.gif",
}

CLASS_VFX = {
    "Barbarian": "vfx/character_vfx/barbarian.jpeg",
    "Bard": "vfx/character_vfx/bard.gif",
    "Cleric": "vfx/character_vfx/cleric.gif",
    "Druid": "vfx/character_vfx/druid.gif",
    "Monk": "vfx/character_vfx/monk.gif",
    "Necromancer": "vfx/character_vfx/necromancer.gif",
    "Paladin": "vfx/character_vfx/paladin.gif",
    "Ranger": "vfx/character_vfx/ranger.gif",
    "Rogue": "vfx/character_vfx/rogue.gif",
    "Deathknight": "vfx/character_vfx/deathknight.jpg",
    "Sorcerer": "vfx/character_vfx/sorcerer.gif",
    "Warlock": "vfx/character_vfx/warlock.gif",
    "Warrior": "vfx/character_vfx/warrior.gif",
    "Wizard": "vfx/character_vfx/wizard.gif",
}

# ── Monk Martial Arts Die ──────────────────────────────────────────────────────
MONK_MARTIAL_ARTS = {1: "1d4", 5: "1d6", 11: "1d8", 17: "1d10"}

def get_monk_die(level):
    """Return the martial arts die for a monk at the given level."""
    die = "1d4"
    for lvl in sorted(MONK_MARTIAL_ARTS.keys()):
        if level >= lvl: die = MONK_MARTIAL_ARTS[lvl]
    return die
