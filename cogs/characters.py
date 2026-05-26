import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from functools import wraps

from _config import AUTO_STARTING_EQUIPMENT, STARTING_GOLD, COMMAND_PREFIX
from data.db import get_db_char, set_char_field, save_character, load_active_characters, set_slots, get_db
from data.helpers import dm_reply

def dm_only(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if not getattr(ctx.bot, "_web_command_active", False) and not any(r.name.lower() in ("dm","dungeon master","game master","gm") for r in ctx.author.roles):
            await ctx.send("❌ Only the DM can use this command."); return
        return await func(self, ctx, *args, **kwargs)
    return wrapper
from data.static_data import (
    RACES, CLASSES, BACKGROUNDS, SUBCLASSES, CLASS_HP, CLASS_STAT_PRIORITY,
    CLASS_STARTING_EQUIPMENT, CLASS_SLOT_TABLE, ARMOR_TABLE, LIGHT_ARMOR, MEDIUM_ARMOR,
    RACE_ITEMS, CLASS_TITLES, modifier, mod_str, prof_bonus, roll_ability_scores,
    get_slots_for_level, get_class_title, CLASS_SAVE_PROFS, CLASS_FEATURES,
    get_weapon_proficiencies, CAMPAIGN_WEAPONS, SKILL_TO_STAT, DRAGONBORN_ANCESTRY,
)


def character_embed(c: dict):
    subclass_str = f" ({c['subclass']})" if c.get("subclass") else ""
    title_str = get_class_title(c["class"], c.get("level", 1))
    embed = discord.Embed(
        title=f"📜 {c['char_name']}",
        description=f"Level {c['level']} {c['race']} **{title_str}**{subclass_str} — *{c['background']}*",
        color=discord.Color.purple()
    )
    stats = (
        f"**STR** {c['strength']} ({mod_str(c['strength'])})  "
        f"**DEX** {c['dexterity']} ({mod_str(c['dexterity'])})  "
        f"**CON** {c['constitution']} ({mod_str(c['constitution'])})\n"
        f"**INT** {c['intelligence']} ({mod_str(c['intelligence'])})  "
        f"**WIS** {c['wisdom']} ({mod_str(c['wisdom'])})  "
        f"**CHA** {c['charisma']} ({mod_str(c['charisma'])})"
    )
    embed.add_field(name="Ability Scores", value=stats, inline=False)
    max_hp = c.get("max_hp") or c["hp"]
    embed.add_field(name="HP", value=f"{c['hp']} / {max_hp}", inline=True)
    embed.add_field(name="AC", value=str(c.get("ac", 10)), inline=True)
    embed.add_field(name="Prof Bonus", value=f"+{prof_bonus(c['level'])}", inline=True)

    # Saving throw proficiencies
    from data.static_data import CLASS_SAVE_PROFS as _CSP
    save_profs = _CSP.get(c["class"], set())
    if save_profs:
        embed.add_field(name="Save Proficiencies", value=", ".join(s.title() for s in sorted(save_profs)), inline=True)

    # Equipment Paperdoll
    weapon = (c.get("equipped_weapon") or "—").title()
    armor = (c.get("equipped_armor") or "—").title()
    offhand = (c.get("equipped_offhand") or "—").title()
    head = (c.get("equipped_head") or "—").title()
    hands = (c.get("equipped_hands") or "—").title()
    feet = (c.get("equipped_feet") or "—").title()
    ring = (c.get("equipped_ring") or "—").title()
    paperdoll = (
        f"👑 Head:  {head}\n"
        f"🦺 Chest: {armor}\n"
        f"🧤 Hands: {hands}\n"
        f"👢 Feet:  {feet}\n"
        f"🗡️ Main:  {weapon}\n"
        f"🛡️ Off:   {offhand}\n"
        f"💍 Ring:  {ring}"
    )
    embed.add_field(name="🧍 Equipped Gear", value=paperdoll, inline=False)
    embed.add_field(name="Speed", value="30 ft", inline=True)

    # Spell Slots (for casters)
    from data.db import get_slots
    from data.static_data import get_slots_for_level as _gsfl, CLASS_SPELL_LIST
    if CLASS_SPELL_LIST.get(c["class"]):
        slots = get_slots(c.get("discord_id"))
        if slots:
            slot_str = " | ".join(f"L{i}:{slots[f'slot_{i}']}" for i in range(1, 10) if slots[f"slot_{i}"] > 0)
            if slot_str:
                embed.add_field(name="🔮 Spell Slots", value=slot_str, inline=False)

    # Known Spells
    known = [s.strip() for s in (c.get("known_spells") or "").split(",") if s.strip()]
    if known:
        embed.add_field(name="📖 Known Spells", value=", ".join(s.title() for s in known[:15]) + (f" (+{len(known)-15} more)" if len(known) > 15 else ""), inline=False)

    # Racial Ability
    from data.static_data import RACIAL_ABILITIES
    racial = RACIAL_ABILITIES.get(c.get("race", ""))
    if racial and racial["type"] not in ("passive",):
        used = c.get("racial_uses", 0) or 0
        remaining = "∞" if racial["uses"] == -1 else f"{max(0, racial['uses'] - used)}/{racial['uses']}"
        ancestry_str = f" ({c['dragon_ancestry']})" if c.get("dragon_ancestry") else ""
        embed.add_field(name=f"🧬 {racial['name']}{ancestry_str}", value=f"{remaining} uses", inline=True)

    # Short Rests
    sr_used = c.get("short_rest_used", 0) or 0
    embed.add_field(name="🌗 Short Rests", value=f"{2 - sr_used}/2", inline=True)

    # Hit Dice
    hd_remaining = c.get("hit_dice_remaining") or c["level"]
    from data.static_data import CLASS_HP as _CHP
    hit_die = _CHP.get(c["class"], 8)
    embed.add_field(name="🎲 Hit Dice", value=f"{hd_remaining}/{c['level']} (d{hit_die})", inline=True)

    # Gold
    gold = c.get("gold", 0) or 0
    if gold:
        embed.add_field(name="💰 Gold", value=str(gold), inline=True)

    # Passive Perception
    wis_mod = modifier(c["wisdom"])
    passive_perc = 10 + wis_mod + (prof_bonus(c["level"]) if "perception" in (c.get("skill_profs") or "") else 0)
    embed.add_field(name="👁️ Passive Perception", value=str(passive_perc), inline=True)

    # Inventory (bag — unequipped items)
    inv = c.get("inventory") or ""
    if inv:
        items = [i.strip() for i in inv.split(",") if i.strip()]
        embed.add_field(name="🎒 Bag", value=", ".join(items[:10]) + (f" (+{len(items)-10} more)" if len(items) > 10 else ""), inline=False)

    # Feats
    feats = c.get("feats") or ""
    if feats:
        embed.add_field(name="⚡ Feats", value=feats, inline=False)

    # Conditions
    if c.get("conditions_active"):
        embed.add_field(name="🩸 Conditions", value=c["conditions_active"], inline=False)

    # XP
    from data.static_data import next_level_xp
    embed.add_field(name="⭐ XP", value=f"{c.get('xp',0)} / {next_level_xp(c['level']) or '—'}", inline=True)

    if c.get("concentration"):
        embed.add_field(name="⚠️ Concentrating", value=c["concentration"], inline=True)

    embed.set_footer(text=f"Player: {c['discord_name']}")
    # Class art (main image — bottom, full width)
    import os
    from data.static_data import RACE_VFX, CLASS_VFX
    class_img = CLASS_VFX.get(c.get("class", ""))
    if class_img and os.path.exists(class_img):
        embed.set_image(url=f"attachment://{os.path.basename(class_img)}")
    return embed


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = set()

    @commands.command()
    async def createchar(self, ctx, mode: str = None):
        if ctx.author.id in self.active_sessions:
            await ctx.send("⚠️ You already have a character creation in progress."); return
        self.active_sessions.add(ctx.author.id)
        user = ctx.author
        try:
            if mode and mode.lower().startswith("random"):
                # Parse: !createchar random [caster|melee|healer|tank]
                parts = mode.lower().split()
                category = parts[1] if len(parts) > 1 else None
                ROLE_CLASSES = {
                    "caster": ["Wizard", "Sorcerer", "Necromancer", "Warlock"],
                    "melee": ["Warrior", "Barbarian", "Monk", "Rogue", "Deathknight"],
                    "healer": ["Cleric", "Druid", "Bard"],
                    "tank": ["Warrior", "Paladin", "Deathknight", "Barbarian"],
                    "ranged": ["Ranger", "Wizard", "Sorcerer", "Warlock"],
                }
                if category and category in ROLE_CLASSES:
                    char_class = random.choice(ROLE_CLASSES[category])
                else:
                    char_class = random.choice(CLASSES)
                char_name = random.choice(['Ash','Bran','Cael','Dorn','Eira','Finn','Grim','Hale','Iris','Jax','Kael','Lyra','Mira','Nyx','Orin','Pike','Quinn','Rook','Sage','Thane','Uma','Vex','Wren','Xara','Yara','Zev'])
                race = random.choice(RACES)
                dragon_ancestry = random.choice(list(DRAGONBORN_ANCESTRY.keys())) if race == "Dragonborn" else None
                subs = SUBCLASSES.get(char_class, [])
                subclass = random.choice(subs) if subs else None
                bg = random.choice(BACKGROUNDS)
                scores = roll_ability_scores(char_class)
                con_mod = modifier(scores["Constitution"])
                hp_val = CLASS_HP.get(char_class, 8) + con_mod
                ac_val = 10 + modifier(scores["Dexterity"])
                data = {"discord_id": user.id, "discord_name": str(user), "char_name": char_name,
                        "race": race, "class": char_class, "subclass": subclass, "background": bg,
                        "strength": scores["Strength"], "dexterity": scores["Dexterity"],
                        "constitution": scores["Constitution"], "intelligence": scores["Intelligence"],
                        "wisdom": scores["Wisdom"], "charisma": scores["Charisma"], "hp": hp_val, "ac": ac_val}
                save_character(data)
                import json
                set_char_field(user.id, "original_stats", json.dumps(scores))
                if dragon_ancestry:
                    set_char_field(user.id, "dragon_ancestry", dragon_ancestry)
                set_slots(user.id, get_slots_for_level(char_class, 1))
                equip_msg = ""
                if AUTO_STARTING_EQUIPMENT and char_class in CLASS_STARTING_EQUIPMENT:
                    weapon_key, armor_key, has_shield, items = CLASS_STARTING_EQUIPMENT[char_class]
                    set_char_field(user.id, "equipped_weapon", weapon_key)
                    dex_mod = modifier(scores["Dexterity"])
                    base_ac = ARMOR_TABLE.get(armor_key, 10)
                    if armor_key in LIGHT_ARMOR | {"no armor"}: calc_ac = base_ac + dex_mod
                    elif armor_key in MEDIUM_ARMOR: calc_ac = base_ac + min(dex_mod, 2)
                    else: calc_ac = base_ac
                    if char_class == "Barbarian": calc_ac = 10 + dex_mod + modifier(scores["Constitution"])
                    elif char_class == "Monk": calc_ac = 10 + dex_mod + modifier(scores["Wisdom"])
                    if has_shield: calc_ac += 2
                    set_char_field(user.id, "ac", calc_ac)
                    set_char_field(user.id, "inventory", ", ".join(items))
                    equip_msg = f"\n⚔️ Equipped: **{weapon_key.title()}** | 🛡️ AC: **{calc_ac}**"
                race_info = RACE_ITEMS.get(race)
                if race_info:
                    item_name, desc = race_info
                    inv = [i.strip() for i in (get_db_char(user.id).get("inventory") or "").split(",") if i.strip()]
                    inv.append(item_name)
                    set_char_field(user.id, "inventory", ", ".join(inv))
                embed = character_embed(get_db_char(user.id))
                await ctx.send(f"🎲 **Random character created!**{equip_msg}", embed=embed)
                return

            # Full guided creation via DMs
            dm = await user.create_dm()
            await ctx.send(f"📬 {user.mention} Check your DMs — character creation has begun!")
            await dm.send("⚔️ **Welcome to DnD 5e Character Creation!**\nType `cancel` at any time.\n\u200b")

            def check(m): return m.author == user and isinstance(m.channel, discord.DMChannel)

            async def dm_ask(prompt, valid_options=None):
                if prompt:
                    import time as _time
                    expires = int(_time.time()) + 120
                    await dm.send(f"{prompt}\n\n⏰ Respond before <t:{expires}:R>")
                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=120)
                except asyncio.TimeoutError:
                    await dm.send("⏰ Timed out. Use `!createchar` to start again."); return None
                if msg.content.strip().lower() == "cancel":
                    await dm.send("❌ Cancelled."); return None
                if valid_options:
                    answer = msg.content.strip()
                    match = next((opt for opt in valid_options if opt.lower() == answer.lower()), None)
                    if not match:
                        await dm.send(f"❌ Choose from: {', '.join(valid_options)}")
                        return await dm_ask(prompt, valid_options)
                    return match
                return msg.content.strip()

            char_name = await dm_ask("**Step 1/6 — Name**\nWhat is your character's name?")
            if not char_name: return
            race = await dm_ask(f"**Step 2/6 — Race**\n" + "\n".join(f"• {r}" for r in RACES), RACES)
            if not race: return
            dragon_ancestry = None
            if race == "Dragonborn":
                from data.static_data import DRAGONBORN_ANCESTRY
                anc_list = list(DRAGONBORN_ANCESTRY.keys())
                dragon_ancestry = await dm_ask("**Dragon Ancestry** — Choose your lineage:\n" + "\n".join(f"• {a}" for a in anc_list), anc_list)
                if not dragon_ancestry: return
            char_class = await dm_ask(f"**Step 3/6 — Class**\n" + "\n".join(f"• {c}" for c in CLASSES), CLASSES)
            if not char_class: return
            subs = SUBCLASSES.get(char_class, [])
            subclass = None
            if subs:
                subclass = await dm_ask(f"**Step 4/6 — Subclass**\n" + "\n".join(f"• {s}" for s in subs), subs)
                if not subclass: return
            else:
                await dm.send("**Step 4/6 — Subclass**\nNo subclass options at level 1. Skipping.")
            bg = await dm_ask(f"**Step 5/6 — Background**\n" + "\n".join(f"• {b}" for b in BACKGROUNDS), BACKGROUNDS)
            if not bg: return

            await dm.send("**Step 6/6 — Ability Scores**\nRolling (4d6 drop lowest)...")
            scores = roll_ability_scores(char_class)
            score_lines = "\n".join(f"**{k}:** {v} ({mod_str(v)})" for k, v in scores.items())
            await dm.send(f"🎲 Your rolls (auto-assigned by class priority):\n{score_lines}\n\nType `keep` or `reroll` for one free reroll.")
            resp = await dm_ask("", ["Keep", "Reroll"])
            if not resp: return
            if resp == "Reroll":
                scores = roll_ability_scores(char_class)
                score_lines = "\n".join(f"**{k}:** {v} ({mod_str(v)})" for k, v in scores.items())
                await dm.send(f"🎲 New rolls (auto-assigned by class priority):\n{score_lines}")

            con_mod = modifier(scores["Constitution"])
            hp = CLASS_HP.get(char_class, 8) + con_mod
            ac = 10 + modifier(scores["Dexterity"])
            data = {"discord_id": user.id, "discord_name": str(user), "char_name": char_name,
                    "race": race, "class": char_class, "subclass": subclass, "background": bg,
                    "strength": scores["Strength"], "dexterity": scores["Dexterity"],
                    "constitution": scores["Constitution"], "intelligence": scores["Intelligence"],
                    "wisdom": scores["Wisdom"], "charisma": scores["Charisma"], "hp": hp, "ac": ac}
            save_character(data)
            import json
            set_char_field(user.id, "original_stats", json.dumps(scores))
            if dragon_ancestry:
                set_char_field(user.id, "dragon_ancestry", dragon_ancestry)
            set_slots(user.id, get_slots_for_level(char_class, 1))

            equip_msg = ""
            if AUTO_STARTING_EQUIPMENT and char_class in CLASS_STARTING_EQUIPMENT:
                weapon_key, armor_key, has_shield, items = CLASS_STARTING_EQUIPMENT[char_class]
                set_char_field(user.id, "equipped_weapon", weapon_key)
                dex_mod = modifier(scores["Dexterity"])
                base_ac = ARMOR_TABLE.get(armor_key, 10)
                if armor_key in LIGHT_ARMOR | {"no armor"}: calc_ac = base_ac + dex_mod
                elif armor_key in MEDIUM_ARMOR: calc_ac = base_ac + min(dex_mod, 2)
                else: calc_ac = base_ac
                if char_class == "Barbarian": calc_ac = 10 + dex_mod + modifier(scores["Constitution"])
                elif char_class == "Monk": calc_ac = 10 + dex_mod + modifier(scores["Wisdom"])
                if has_shield: calc_ac += 2
                set_char_field(user.id, "ac", calc_ac)
                set_char_field(user.id, "inventory", ", ".join(items))
                equip_msg = f"\n⚔️ Equipped: **{weapon_key.title()}** | 🛡️ AC: **{calc_ac}** | 🎒 Starting gear granted"

            if STARTING_GOLD > 0:
                set_char_field(user.id, "gold", STARTING_GOLD)

            race_info = RACE_ITEMS.get(race)
            if race_info:
                item_name, desc = race_info
                inv = [i.strip() for i in (get_db_char(user.id).get("inventory") or "").split(",") if i.strip()]
                inv.append(item_name)
                set_char_field(user.id, "inventory", ", ".join(inv))
                equip_msg += f"\n🧬 Racial heirloom: **{item_name}** — {desc}"

            # Backstory
            backstory_text = await dm_ask("**Step 7 — Backstory (optional)**\nWrite your backstory (max 1500 words), or type `skip`.")
            if backstory_text and backstory_text.lower() != "skip":
                word_count = len(backstory_text.split())
                if word_count > 1500:
                    backstory_text = " ".join(backstory_text.split()[:1500])
                set_char_field(user.id, "backstory", backstory_text)
                equip_msg += f"\n📜 Backstory saved ({len(backstory_text.split())} words)"

            # Fears & Dreams
            char_fear = await dm_ask("**Step 8 — Character Fear**\nWhat is your CHARACTER afraid of?")
            if not char_fear: return
            set_char_field(user.id, "char_fear", char_fear[:255])
            player_fear = await dm_ask("**Step 9 — Player Fear**\nWhat are YOU (the real you) afraid of?")
            if not player_fear: return
            set_char_field(user.id, "player_fear", player_fear[:255])
            char_dream = await dm_ask("**Final — Hope/Dream**\nWhat does your character want more than anything?")
            if not char_dream: return
            set_char_field(user.id, "char_dream", char_dream[:255])
            await dm.send("✅ Got it. These details will shape your experience. Let's begin.")

            embed = character_embed(get_db_char(user.id))
            await dm.send(f"✅ **Character created!**{equip_msg}", embed=embed)
        finally:
            self.active_sessions.discard(user.id)

    @commands.command(aliases=["mychar"])
    async def char(self, ctx, *, target: str = None):
        """View a character sheet. DMs can view any player. Players see their own via DM."""
        from data.helpers import is_dm
        import os, discord as _d
        from data.static_data import RACE_VFX, CLASS_VFX
        c = None
        if target and is_dm(ctx):
            # Try @mention first
            if target.startswith("<@") and target.endswith(">"):
                member_id = int(target.strip("<@!>"))
                c = get_db_char(member_id)
            else:
                # Try character name lookup
                from data.db import get_db
                conn = get_db(); cur = conn.cursor(dictionary=True)
                cur.execute("SELECT discord_id FROM characters WHERE LOWER(char_name) = LOWER(%s)", (target,))
                row = cur.fetchone(); cur.close(); conn.close()
                if row:
                    c = get_db_char(row["discord_id"])
            if not c: await ctx.send(f"❌ No character found for `{target}`."); return
            files = self._get_char_files(c)
            if files:
                await ctx.send(embed=character_embed(c), files=files)
            else:
                await ctx.send(embed=character_embed(c))
        else:
            # Player viewing own sheet — send to DMs
            c = get_db_char(ctx.author.id)
            if not c: await ctx.send("No character found. Use `!createchar`."); return
            files = self._get_char_files(c)
            await dm_reply(ctx, embed=character_embed(c), file=files[0] if len(files) == 1 else None)
            # dm_reply doesn't support multiple files, send separately for players
            if len(files) > 1:
                try:
                    await ctx.author.send(files=files)
                except: pass

    def _get_char_files(self, c):
        """Get class image file for character embed."""
        import os, discord as _d
        from data.static_data import CLASS_VFX
        files = []
        class_img = CLASS_VFX.get(c.get("class", ""))
        if class_img and os.path.exists(class_img) and os.path.getsize(class_img) < 8_000_000:
            files.append(_d.File(class_img, filename=os.path.basename(class_img)))
        return files

    @commands.command()
    async def party(self, ctx):
        chars = load_active_characters()
        if not chars: await ctx.send("No active characters."); return
        embed = discord.Embed(title="⚔️ The Party", color=discord.Color.dark_purple())
        for c in chars:
            max_hp = c.get("max_hp") or c["hp"]
            title = get_class_title(c["class"], c.get("level", 1))
            subclass_str = f" ({c['subclass']})" if c.get("subclass") else ""
            val = f"Level {c['level']} {c['race']} {title}{subclass_str}\nHP: {c['hp']}/{max_hp} | AC: {c.get('ac',10)}"
            embed.add_field(name=c["char_name"], value=val, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @dm_only
    async def deletechar(self, ctx):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM characters WHERE discord_id = %s", (ctx.author.id,))
        conn.commit(); cur.close(); conn.close()
        await ctx.send("🗑️ Character deleted.")

    @commands.command()
    async def backstory(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        c = get_db_char(target.id)
        if not c: await ctx.send("No character found."); return
        bs = c.get("backstory")
        if not bs: await ctx.send(f"**{c['char_name']}** has no backstory. Use `!setbackstory <text>`."); return
        embed = discord.Embed(title=f"📜 {c['char_name']}'s Backstory", description=bs[:4096], color=discord.Color.dark_purple())
        await dm_reply(ctx, embed=embed)

    @commands.command()
    async def setbackstory(self, ctx, *, text: str):
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        if len(text.split()) > 1500: await ctx.send("❌ Max 1500 words."); return
        set_char_field(ctx.author.id, "backstory", text)
        await ctx.send(f"📜 **{c['char_name']}**'s backstory saved ({len(text.split())} words).")

    @commands.command()
    async def features(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        class_feats = CLASS_FEATURES.get(c["class"], {})
        embed = discord.Embed(title=f"📋 {c['char_name']} — {c['class']} Features (Level {c['level']})", color=discord.Color.dark_teal())
        for lvl in sorted(k for k in class_feats if k <= c["level"]):
            items = class_feats[lvl]
            if items: embed.add_field(name=f"Level {lvl}", value="\n".join(f"• {f}" for f in items), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def profs(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        embed = discord.Embed(title=f"📋 {c['char_name']}'s Proficiencies", color=discord.Color.dark_teal())
        save_profs = CLASS_SAVE_PROFS.get(c["class"], set())
        embed.add_field(name="Saving Throws", value=", ".join(s.title() for s in sorted(save_profs)) or "None", inline=False)
        weapons = get_weapon_proficiencies(c["class"], c["race"], c.get("notes", ""))
        visible_weapons = weapons - set(CAMPAIGN_WEAPONS.keys())
        embed.add_field(name="Weapons", value=", ".join(sorted(visible_weapons)).title() or "None", inline=False)
        embed.add_field(name="Skill Proficiencies", value=(c.get("skill_profs") or "None").title(), inline=False)
        embed.add_field(name="Expertise", value=(c.get("expertise") or "None").title(), inline=False)
        embed.add_field(name="Tools", value=c.get("tool_profs") or "None", inline=True)
        embed.add_field(name="Languages", value=c.get("languages") or "Common", inline=True)
        await dm_reply(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Characters(bot))
