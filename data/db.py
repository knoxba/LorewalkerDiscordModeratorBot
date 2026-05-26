import mysql.connector
from _config import DB


def get_db():
    return mysql.connector.connect(**DB)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            discord_id BIGINT NOT NULL UNIQUE,
            discord_name VARCHAR(100),
            char_name VARCHAR(100),
            race VARCHAR(50),
            class VARCHAR(50),
            subclass VARCHAR(100),
            background VARCHAR(50),
            strength INT, dexterity INT, constitution INT,
            intelligence INT, wisdom INT, charisma INT,
            hp INT, max_hp INT,
            ac INT DEFAULT 10,
            level INT DEFAULT 1,
            xp INT DEFAULT 0,
            notes TEXT,
            equipped_weapon VARCHAR(50) DEFAULT NULL,
            conditions_active TEXT DEFAULT NULL,
            concentration VARCHAR(100) DEFAULT NULL
        )
    """)
    for col, definition in [
        ("subclass",          "VARCHAR(100) DEFAULT NULL"),
        ("max_hp",            "INT DEFAULT 0"),
        ("ac",                "INT DEFAULT 10"),
        ("xp",                "INT DEFAULT 0"),
        ("equipped_weapon",   "VARCHAR(50) DEFAULT NULL"),
        ("conditions_active", "TEXT DEFAULT NULL"),
        ("concentration",     "VARCHAR(100) DEFAULT NULL"),
        ("gold",              "INT DEFAULT 0"),
        ("inspiration",       "TINYINT(1) DEFAULT 0"),
        ("hit_dice_remaining","INT DEFAULT 1"),
        ("known_spells",      "TEXT DEFAULT NULL"),
        ("inventory",         "TEXT DEFAULT NULL"),
        ("class_resources",   "TEXT DEFAULT NULL"),
        ("second_class",      "VARCHAR(50) DEFAULT NULL"),
        ("second_level",      "INT DEFAULT 0"),
        ("attuned_items",     "TEXT DEFAULT NULL"),
        ("tool_profs",        "TEXT DEFAULT NULL"),
        ("languages",         "TEXT DEFAULT NULL"),
        ("prepared_spells",   "TEXT DEFAULT NULL"),
        ("skill_profs",       "TEXT DEFAULT NULL"),
        ("expertise",         "TEXT DEFAULT NULL"),
        ("pp",                "INT DEFAULT 0"),
        ("sp",                "INT DEFAULT 0"),
        ("cp",                "INT DEFAULT 0"),
        ("temp_hp",           "INT DEFAULT 0"),
        ("exhaustion",        "INT DEFAULT 0"),
        ("dread",             "INT DEFAULT 0"),
        ("backstory",         "TEXT DEFAULT NULL"),
        ("char_fear",         "VARCHAR(255) DEFAULT NULL"),
        ("player_fear",       "VARCHAR(255) DEFAULT NULL"),
        ("char_dream",        "VARCHAR(255) DEFAULT NULL"),
        ("active",            "TINYINT(1) DEFAULT 0"),
        ("equipped_armor",    "VARCHAR(100) DEFAULT NULL"),
        ("equipped_offhand",  "VARCHAR(100) DEFAULT NULL"),
        ("equipped_head",     "VARCHAR(100) DEFAULT NULL"),
        ("equipped_hands",    "VARCHAR(100) DEFAULT NULL"),
        ("equipped_feet",     "VARCHAR(100) DEFAULT NULL"),
        ("equipped_ring",     "VARCHAR(100) DEFAULT NULL"),
        ("racial_uses",       "INT DEFAULT 0"),
        ("short_rest_used",   "INT DEFAULT 0"),
        ("long_rest_used",    "INT DEFAULT 0"),
        ("dragon_ancestry",   "VARCHAR(50) DEFAULT NULL"),
        ("feats",             "TEXT DEFAULT NULL"),
        ("original_stats",    "TEXT DEFAULT NULL"),
    ]:
        try:
            cur.execute(f"ALTER TABLE characters ADD COLUMN {col} {definition}")
        except Exception:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS spell_slots (
            discord_id BIGINT PRIMARY KEY,
            slot_1 INT DEFAULT 0, slot_2 INT DEFAULT 0, slot_3 INT DEFAULT 0,
            slot_4 INT DEFAULT 0, slot_5 INT DEFAULT 0, slot_6 INT DEFAULT 0,
            slot_7 INT DEFAULT 0, slot_8 INT DEFAULT 0, slot_9 INT DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def get_db_char(discord_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM characters WHERE discord_id = %s", (discord_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def set_char_field(discord_id, field, value):
    allowed = {"hp","max_hp","ac","level","xp","notes","strength","dexterity","constitution",
               "intelligence","wisdom","charisma","equipped_weapon","conditions_active","concentration","subclass",
               "gold","inspiration","hit_dice_remaining","known_spells","inventory",
               "class_resources","second_class","second_level","attuned_items","tool_profs","languages","prepared_spells",
               "skill_profs","expertise","pp","sp","cp","temp_hp","exhaustion","dread","backstory",
               "char_fear","player_fear","char_dream","active",
               "equipped_armor","equipped_offhand","equipped_head","equipped_hands","equipped_feet","equipped_ring"}
    if field not in allowed:
        return False
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE characters SET {field} = %s WHERE discord_id = %s", (value, discord_id))
    conn.commit()
    cur.close()
    conn.close()
    return True


def save_character(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM characters WHERE discord_id = %s", (data["discord_id"],))
    cur.execute("""
        INSERT INTO characters
        (discord_id, discord_name, char_name, race, class, subclass, background,
         strength, dexterity, constitution, intelligence, wisdom, charisma,
         hp, max_hp, ac, level, xp, hit_dice_remaining)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["discord_id"], data["discord_name"], data["char_name"],
        data["race"], data["class"], data.get("subclass"), data["background"],
        data["strength"], data["dexterity"], data["constitution"],
        data["intelligence"], data["wisdom"], data["charisma"],
        data["hp"], data["hp"], data.get("ac", 10), 1, 0, 1
    ))
    conn.commit()
    cur.close()
    conn.close()


def get_slots(discord_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM spell_slots WHERE discord_id = %s", (discord_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def set_slots(discord_id, slots_list):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("REPLACE INTO spell_slots VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (discord_id, *slots_list))
    conn.commit()
    cur.close()
    conn.close()


def load_all_characters():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM characters ORDER BY level DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def load_active_characters():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM characters WHERE active = 1 ORDER BY level DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
