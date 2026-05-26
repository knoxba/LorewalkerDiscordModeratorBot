import random
import discord
from discord.ext import commands

from _config import ENABLE_DURABILITY
import random as _rand
from data.db import get_db_char, set_char_field
from data.static_data import (
    WEAPONS, WEAPON_RARITY, CAMPAIGN_WEAPONS, ARMOR_TABLE, LIGHT_ARMOR, MEDIUM_ARMOR, HEAVY_ARMOR,
    CLASS_ARMOR_PROF, get_armor_category, get_weapon_proficiencies, modifier,
    UNTRADEABLE_ITEMS, CAMPAIGN_ARMOR, ARMOR_RARITY, get_item_emoji,
    get_item_info, ITEM_DATABASE,
)
from data.helpers import dm_reply


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_trades = {}
        self.combat_sessions = None  # Will reference combat cog's sessions

    def _in_combat(self, guild_id):
        combat = self.bot.get_cog("Combat")
        return combat and guild_id in combat.combat_sessions and combat.combat_sessions[guild_id].get("order")

    @commands.command()
    async def inventory(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        # Extract gold entries from inventory and add to currency display
        import re
        extra_gold = 0
        filtered_items = []
        for i in items:
            gold_match = re.match(r'^(\d+)\s*gold$', i.strip(), re.IGNORECASE)
            if gold_match:
                extra_gold += int(gold_match.group(1))
            else:
                filtered_items.append(i)
        total_gold = (c.get('gold', 0) or 0) + extra_gold
        embed = discord.Embed(title=f"🎒 {c['char_name']}'s Inventory", color=discord.Color.dark_gold())
        embed.add_field(name="Currency", value=f"🪙 {c.get('pp',0)} pp  🌕 {total_gold} gp  ⚪ {c.get('sp',0)} sp  🟠 {c.get('cp',0)} cp", inline=False)
        embed.add_field(name="Items", value="\n".join(f"{get_item_emoji(i)} {i}" for i in filtered_items) if filtered_items else "*(empty)*", inline=False)
        await dm_reply(ctx, embed=embed)

    @commands.command()
    async def equip(self, ctx, *, item_name: str):
        """Equip an item. Use: !equip <item> or !equip <slot> <item>"""
        from data.static_data import ITEM_SLOT
        key = item_name.lower().strip()
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return

        # Check if first word is a slot name
        VALID_SLOTS = {"weapon", "armor", "offhand", "head", "hands", "feet", "ring"}
        parts = key.split(None, 1)
        explicit_slot = None
        if parts[0] in VALID_SLOTS:
            explicit_slot = parts[0]
            if len(parts) > 1:
                key = parts[1]
            else:
                # No item specified — find first item in inventory for this slot
                from data.static_data import ITEM_SLOT
                items = [i.strip().lower() for i in (c.get("inventory") or "").split(",") if i.strip()]
                match = next((i for i in items if ITEM_SLOT.get(i) == explicit_slot), None)
                if not match:
                    await ctx.send(f"❌ No **{explicit_slot}** item found in inventory."); return
                key = match

        # Check inventory
        items = [i.strip().lower() for i in (c.get("inventory") or "").split(",") if i.strip()]
        if key not in items:
            await ctx.send(f"❌ **{c['char_name']}** doesn't have **{key.title()}** in inventory."); return

        # Determine slot
        is_weapon = key in WEAPONS or key in CAMPAIGN_WEAPONS
        is_armor = key in CAMPAIGN_ARMOR or key in ARMOR_TABLE
        slot = explicit_slot or ITEM_SLOT.get(key) or ("weapon" if is_weapon else "armor" if is_armor else None)
        if not slot:
            await ctx.send(f"❌ **{key.title()}** is not equippable. Use `/useitem` for consumables."); return

        db_field = f"equipped_{slot}" if slot != "weapon" else "equipped_weapon"

        if slot == "weapon":
            if key not in get_weapon_proficiencies(c["class"], c["race"], c.get("notes", "")):
                await ctx.send(f"❌ **{c['char_name']}** is not proficient with **{key.title()}**."); return
            set_char_field(ctx.author.id, "equipped_weapon", key)
            base_key = CAMPAIGN_WEAPONS.get(key, key)
            damage, props = WEAPONS.get(key) or WEAPONS.get(base_key, ("?", "?"))
            rarity_info = WEAPON_RARITY.get(key)
            rarity_tag = f" [{rarity_info[0]}]" if rarity_info else ""
            await ctx.send(f"🗡️ **{c['char_name']}** equipped **{key.title()}**{rarity_tag} — {damage} | {props}")

        elif slot == "armor":
            base_armor = CAMPAIGN_ARMOR.get(key, key)
            class_armor = CLASS_ARMOR_PROF.get(c["class"], set())
            can_wear = False
            if base_armor in LIGHT_ARMOR and "light" in class_armor: can_wear = True
            elif base_armor in MEDIUM_ARMOR and "medium" in class_armor: can_wear = True
            elif base_armor in HEAVY_ARMOR and "heavy" in class_armor: can_wear = True
            elif base_armor == "padded" and "light" in class_armor: can_wear = True
            notes = (c.get("notes") or "").lower()
            if "light armor proficiency" in notes and base_armor in LIGHT_ARMOR: can_wear = True
            if "medium armor proficiency" in notes and base_armor in MEDIUM_ARMOR: can_wear = True
            if "heavy armor proficiency" in notes and base_armor in HEAVY_ARMOR: can_wear = True
            if not can_wear:
                await ctx.send(f"❌ **{c['char_name']}** is not proficient with **{key.title()}**."); return
            dex_mod = modifier(c["dexterity"])
            base_ac = ARMOR_TABLE.get(base_armor, 10)
            if base_armor in LIGHT_ARMOR or base_armor == "padded": new_ac = base_ac + dex_mod
            elif base_armor in MEDIUM_ARMOR: new_ac = base_ac + min(dex_mod, 2)
            else: new_ac = base_ac
            if c.get("equipped_offhand") == "shield": new_ac += 2
            set_char_field(ctx.author.id, "equipped_armor", key)
            set_char_field(ctx.author.id, "ac", new_ac)
            rarity_info = ARMOR_RARITY.get(key)
            rarity_tag = f" [{rarity_info[0]}]" if rarity_info else ""
            await ctx.send(f"🦺 **{c['char_name']}** equipped **{key.title()}**{rarity_tag} — AC: **{new_ac}**")

        else:
            # head, hands, feet, ring, offhand
            set_char_field(ctx.author.id, db_field, key)
            rarity_info = ARMOR_RARITY.get(key) or WEAPON_RARITY.get(key)
            rarity_tag = f" [{rarity_info[0]}]" if rarity_info else ""
            slot_emoji = {"head":"🪖","hands":"🧤","feet":"👢","ring":"💍","offhand":"🛡️"}.get(slot, "✨")
            await ctx.send(f"{slot_emoji} **{c['char_name']}** equipped **{key.title()}**{rarity_tag} to **{slot}** slot.")

    @commands.command()
    async def unequip(self, ctx, slot: str = "weapon"):
        """Unequip a slot. Use: !unequip <slot> (weapon/armor/head/hands/feet/ring/offhand)"""
        VALID_SLOTS = {"weapon", "armor", "offhand", "head", "hands", "feet", "ring"}
        slot = slot.lower().strip()
        if slot not in VALID_SLOTS:
            await ctx.send(f"❌ Invalid slot. Options: {', '.join(VALID_SLOTS)}"); return
        db_field = f"equipped_{slot}" if slot != "weapon" else "equipped_weapon"
        c = get_db_char(ctx.author.id)
        if not c: return
        current = c.get(db_field)
        if not current:
            await ctx.send(f"❌ Nothing equipped in **{slot}** slot."); return
        set_char_field(ctx.author.id, db_field, None)
        # Recalc AC if removing armor
        if slot == "armor":
            dex_mod = modifier(c["dexterity"])
            new_ac = 10 + dex_mod
            if c.get("equipped_offhand") == "shield": new_ac += 2
            set_char_field(ctx.author.id, "ac", new_ac)
        await ctx.send(f"✅ **{c['char_name']}** unequipped **{current.title()}** from **{slot}** slot.")

    @commands.command()
    async def weapon(self, ctx, *, name: str):
        key = name.lower()
        if key not in WEAPONS: await ctx.send("❌ Unknown weapon."); return
        if key in CAMPAIGN_WEAPONS:
            c = get_db_char(ctx.author.id)
            items = [i.strip().lower() for i in (c.get("inventory") or "").split(",") if i.strip()] if c else []
            if key not in items: await ctx.send("❌ Unknown weapon."); return
        damage, props = WEAPONS[key]
        rarity_info = WEAPON_RARITY.get(key)
        if rarity_info:
            embed = discord.Embed(title=f"⚔️ {name.title()}", color=discord.Color(rarity_info[1]))
            embed.add_field(name="Rarity", value=rarity_info[0], inline=True)
        else:
            embed = discord.Embed(title=f"⚔️ {name.title()}", color=discord.Color.dark_gold())
            embed.add_field(name="Rarity", value="Common", inline=True)
        embed.add_field(name="Damage", value=damage, inline=True)
        embed.add_field(name="Properties", value=props, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def setac(self, ctx, armor: str):
        key = armor.lower()
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        category = get_armor_category(key)
        # Build effective armor proficiencies (class + feats)
        armor_profs = set(CLASS_ARMOR_PROF.get(c["class"], set()))
        notes = (c.get("notes") or "").lower()
        if "[feat] light armor proficiency" in notes: armor_profs.add("light")
        if "[feat] medium armor proficiency" in notes: armor_profs |= {"medium", "shield"}
        if "[feat] heavy armor proficiency" in notes: armor_profs.add("heavy")
        if category and category not in armor_profs:
            await ctx.send(f"❌ **{c['char_name']}** ({c['class']}) is not proficient with **{category} armor**."); return
        if key == "shield":
            if "shield" not in armor_profs:
                await ctx.send(f"❌ Not proficient with shields."); return
            new_ac = c.get("ac", 10) + 2
            set_char_field(ctx.author.id, "ac", new_ac)
            await ctx.send(f"🛡️ Shield equipped. AC: **{new_ac}**."); return
        if key not in ARMOR_TABLE: await ctx.send("❌ Unknown armor."); return
        base = ARMOR_TABLE[key]
        dex_mod = modifier(c["dexterity"])
        if key in LIGHT_ARMOR | {"no armor"}: new_ac = base + dex_mod
        elif key in MEDIUM_ARMOR: new_ac = base + min(dex_mod, 2)
        else: new_ac = base
        set_char_field(ctx.author.id, "ac", new_ac)
        await ctx.send(f"🛡️ **{c['char_name']}** equipped **{armor.title()}**. AC: **{new_ac}**")

    @commands.command()
    async def ac(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        await ctx.send(f"🛡️ **{c['char_name']}** AC: **{c.get('ac', 10)}**")

    @commands.command()
    async def additem(self, ctx, *, item: str):
        c = get_db_char(ctx.author.id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        items.append(item.strip())
        set_char_field(ctx.author.id, "inventory", ", ".join(items))
        await ctx.send(f"🎒 **{item}** added.")

    @commands.command()
    async def removeitem(self, ctx, *, item: str):
        c = get_db_char(ctx.author.id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        match = next((i for i in items if i.lower() == item.lower()), None)
        if not match: await ctx.send(f"❌ **{item}** not found."); return
        items.remove(match)
        set_char_field(ctx.author.id, "inventory", ", ".join(items) if items else None)
        await ctx.send(f"🎒 **{match}** removed.")

    # ── Gold ───────────────────────────────────────────────────────────────────

    @commands.command()
    async def gold(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        await dm_reply(ctx, content=f"💰 **{c['char_name']}**: {c.get('gold',0)} gp, {c.get('sp',0)} sp, {c.get('cp',0)} cp")

    @commands.command()
    async def convert(self, ctx):
        """Auto-convert currencies up. 10cp→1sp, 10sp→1gp, 10gp→1pp."""
        c = get_db_char(ctx.author.id)
        if not c: return
        import re
        # First, extract any "X gold" from inventory into the gold field
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        extra_gold = 0
        filtered = []
        for i in items:
            gold_match = re.match(r'^(\d+)\s*gold$', i.strip(), re.IGNORECASE)
            if gold_match:
                extra_gold += int(gold_match.group(1))
            else:
                filtered.append(i)
        if extra_gold:
            set_char_field(ctx.author.id, "inventory", ", ".join(filtered))
        # Now convert
        cp = c.get("cp", 0) or 0
        sp = c.get("sp", 0) or 0
        gp = (c.get("gold", 0) or 0) + extra_gold
        pp = c.get("pp", 0) or 0
        sp += cp // 10; cp = cp % 10
        gp += sp // 10; sp = sp % 10
        pp += gp // 10; gp = gp % 10
        set_char_field(ctx.author.id, "cp", cp)
        set_char_field(ctx.author.id, "sp", sp)
        set_char_field(ctx.author.id, "gold", gp)
        set_char_field(ctx.author.id, "pp", pp)
        await ctx.send(f"💱 Converted! 🪙 {pp} pp  🌕 {gp} gp  ⚪ {sp} sp  🟠 {cp} cp")

    @commands.command()
    async def about(self, ctx, *, item_name: str):
        """Look up any item — description, type, effect."""
        info = get_item_info(item_name)
        if not info:
            await ctx.send(f"❌ Unknown item: `{item_name}`. Check spelling."); return
        emoji = get_item_emoji(item_name)
        rarity = info.get("rarity", "Common")
        rarity_colors = {"Common": 0x9e9e9e, "Uncommon": 0x2ecc71, "Rare": 0x3498db, "Very Rare": 0x9b59b6, "Legendary": 0xe67e22}
        embed = discord.Embed(title=f"{emoji} {item_name.title()}", color=rarity_colors.get(rarity, 0x9e9e9e))
        embed.add_field(name="Type", value=info["type"].title(), inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        usability = []
        if info.get("equippable"): usability.append("⚔️ Equippable")
        if info.get("useable"): usability.append("🧪 Useable")
        if not usability: usability.append("📦 Passive")
        embed.add_field(name="Usage", value=" / ".join(usability), inline=True)
        embed.add_field(name="Description", value=f"*{info['description']}*", inline=False)
        embed.add_field(name="Effect", value=info["effect"], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def addgold(self, ctx, amount: int, denomination: str = "gp"):
        denom = denomination.lower()
        field = "gold" if denom == "gp" else denom
        if field not in ("gold","pp","sp","cp"): await ctx.send("❌ Use pp/gp/sp/cp."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        set_char_field(ctx.author.id, field, (c.get(field) or 0) + amount)
        await ctx.send(f"💰 +{amount} {denom}")

    @commands.command()
    async def removegold(self, ctx, amount: int, denomination: str = "gp"):
        denom = denomination.lower()
        field = "gold" if denom == "gp" else denom
        if field not in ("gold","pp","sp","cp"): return
        c = get_db_char(ctx.author.id)
        if not c: return
        current = c.get(field) or 0
        if amount > current: await ctx.send(f"❌ Only have {current} {denom}."); return
        set_char_field(ctx.author.id, field, current - amount)
        await ctx.send(f"💰 -{amount} {denom}")

    # ── Potions & Resurrection ─────────────────────────────────────────────────

    @commands.command()
    async def usepotion(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        potions = [i for i in items if i.lower() == "health potion"]
        if not potions: await ctx.send(f"❌ No health potions."); return
        items.remove(potions[0])
        set_char_field(ctx.author.id, "inventory", ", ".join(items) if items else None)
        rolls = [random.randint(1, 4), random.randint(1, 4)]
        heal_amt = sum(rolls) + 2
        max_hp = c.get("max_hp") or c["hp"]
        new_hp = min(max_hp, c["hp"] + heal_amt)
        set_char_field(ctx.author.id, "hp", new_hp)
        remaining = len([i for i in items if i.lower() == "health potion"])
        await ctx.send(f"🧪 **{c['char_name']}** drinks a potion! Heals `[{rolls[0]},{rolls[1]}]+2` = **{heal_amt} HP**. HP: **{new_hp}/{max_hp}**. Potions: **{remaining}**")

    @commands.command()
    async def useitem(self, ctx, *, item_name: str):
        """Use a consumable item from your inventory."""
        from data.static_data import get_item_info, get_slots_for_level
        from data.db import get_slots, set_slots
        c = get_db_char(ctx.author.id)
        if not c: return
        key = item_name.lower().strip()
        info = get_item_info(key)
        if not info or not info.get("useable"):
            await ctx.send(f"❌ **{item_name.title()}** is not a useable item."); return
        # Check inventory
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        match = next((i for i in items if i.lower() == key), None)
        if not match:
            await ctx.send(f"❌ You don't have **{item_name.title()}** in your inventory."); return
        # Remove from inventory
        items.remove(match)
        set_char_field(ctx.author.id, "inventory", ", ".join(items) if items else None)
        max_hp = c.get("max_hp") or c["hp"]
        emoji = get_item_emoji(key)
        msg = f"{emoji} **{c['char_name']}** uses **{item_name.title()}**!\n"

        # Apply effects by item
        if key == "bandage":
            heal = random.randint(1, 4)
            new_hp = min(max_hp, c["hp"] + heal)
            set_char_field(ctx.author.id, "hp", new_hp)
            msg += f"❤️ Heals **{heal} HP** → {new_hp}/{max_hp}"

        elif key == "antidote vial":
            conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
            conds = [x for x in conds if x.lower() != "poisoned"]
            set_char_field(ctx.author.id, "conditions_active", ", ".join(conds) if conds else None)
            msg += "🧪 **Poisoned** condition removed!"

        elif key == "smoke bomb":
            msg += "💨 Disengaged! No opportunity attacks this turn."

        elif key == "tincture of clarity":
            conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
            conds = [x for x in conds if x.lower() not in ("frightened", "charmed")]
            set_char_field(ctx.author.id, "conditions_active", ", ".join(conds) if conds else None)
            msg += "💎 **Frightened** and **Charmed** removed! Advantage on next WIS save."

        elif key == "essence of forgotten breath":
            slots = get_slots_for_level(c["class"], c["level"])
            set_slots(ctx.author.id, slots)
            msg += "✨ All spell slots restored!"

        elif key == "vial of spatial mending":
            rolls = [random.randint(1, 8) for _ in range(3)]
            heal = sum(rolls)
            new_hp = min(max_hp, c["hp"] + heal)
            set_char_field(ctx.author.id, "hp", new_hp)
            conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
            conds = [x for x in conds if x.lower() not in ("restrained", "prone")]
            set_char_field(ctx.author.id, "conditions_active", ", ".join(conds) if conds else None)
            msg += f"❤️ Heals `[{','.join(str(r) for r in rolls)}]` = **{heal} HP** → {new_hp}/{max_hp}\n🔓 Restrained/Prone removed!"

        elif key == "heart of the house":
            set_char_field(ctx.author.id, "temp_hp", max(c.get("temp_hp", 0) or 0, 20))
            msg += "🫀 Gained **20 temp HP**. Immune to frightened for 1 hour."

        elif key == "soul fragment":
            msg += "👻 +**1d6** to your next attack roll or saving throw. (Tell DM when you use it.)"

        elif key == "whetstone":
            msg += "🪨 Next weapon attack deals **+2 damage**. (Tell DM when you attack.)"

        else:
            msg += f"Effect: {info['effect']}"

        await ctx.send(msg)

    @commands.command()
    async def resurrect(self, ctx, member: discord.Member):
        if member.id == ctx.author.id: await ctx.send("❌ Can't self-resurrect."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        scrolls = [i for i in items if i.lower() == "resurrection scroll"]
        if not scrolls: await ctx.send("❌ No Resurrection Scroll."); return
        target = get_db_char(member.id)
        if not target or target["hp"] > 0: await ctx.send("❌ Target is not downed."); return
        idx = next(i for i, item in enumerate(items) if item.lower() == "resurrection scroll")
        items[idx] = "Blank Scroll"
        set_char_field(ctx.author.id, "inventory", ", ".join(items))
        set_char_field(member.id, "hp", 1)
        import os
        gif_path = "vfx/spell_vfx/resurrect_necromancy.gif"
        if os.path.exists(gif_path):
            await ctx.send(
                f"📜✨ **{c['char_name']}** uses their Resurrection Scroll!\n💖 **{target['char_name']}** gasps back to life at **1 HP**.",
                file=discord.File(gif_path, filename="resurrect.gif")
            )
        else:
            await ctx.send(f"📜✨ **{c['char_name']}** uses their Resurrection Scroll!\n💖 **{target['char_name']}** gasps back to life at **1 HP**.")

    # ── Trading ────────────────────────────────────────────────────────────────

    @commands.command()
    async def trade(self, ctx, member: discord.Member, *, item: str):
        if member.id == ctx.author.id: return
        if self._in_combat(ctx.guild.id): await ctx.send("❌ No trading during combat."); return
        if item.lower() in UNTRADEABLE_ITEMS: await ctx.send(f"❌ **{item}** cannot be traded."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        match = next((i for i in items if i.lower() == item.lower()), None)
        if not match: await ctx.send(f"❌ Don't have **{item}**."); return
        guild_trades = self.pending_trades.setdefault(ctx.guild.id, {})
        guild_trades[member.id] = {"from": ctx.author.id, "item": match}
        await ctx.send(f"🔄 **{c['char_name']}** offers **{match}** to {member.mention}. Type `!accepttrade` or `!declinetrade`.")

    @commands.command()
    async def accepttrade(self, ctx):
        guild_trades = self.pending_trades.get(ctx.guild.id, {})
        trade_info = guild_trades.get(ctx.author.id)
        if not trade_info: await ctx.send("❌ No pending trade."); return
        sender = get_db_char(trade_info["from"])
        item = trade_info["item"]
        sender_items = [i.strip() for i in (sender.get("inventory") or "").split(",") if i.strip()]
        if item not in sender_items: await ctx.send("❌ Sender no longer has item."); del guild_trades[ctx.author.id]; return
        sender_items.remove(item)
        set_char_field(trade_info["from"], "inventory", ", ".join(sender_items) if sender_items else None)
        receiver = get_db_char(ctx.author.id)
        recv_items = [i.strip() for i in (receiver.get("inventory") or "").split(",") if i.strip()]
        recv_items.append(item)
        set_char_field(ctx.author.id, "inventory", ", ".join(recv_items))
        del guild_trades[ctx.author.id]
        await ctx.send(f"✅ **{item}** moved from **{sender['char_name']}** → **{receiver['char_name']}**.")

    @commands.command()
    async def declinetrade(self, ctx):
        guild_trades = self.pending_trades.get(ctx.guild.id, {})
        if ctx.author.id not in guild_trades: return
        del guild_trades[ctx.author.id]
        await ctx.send("❌ Trade declined.")


async def setup(bot):
    await bot.add_cog(Inventory(bot))
