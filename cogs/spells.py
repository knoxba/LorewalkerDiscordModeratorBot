import random
import os
import discord
from discord.ext import commands

from _config import DREAD_SECRET_THRESHOLD
from data.db import get_db_char, set_char_field, get_slots, set_slots
from data.helpers import dm_reply
from data.static_data import (
    SPELLS, CASTABLE_SPELLS, CLASS_SCHOOLS, SPELLCASTING_STAT, SCHOOL_GIF, SPELL_GIF_OVERRIDE,
    modifier, mod_str, prof_bonus, get_slots_for_level, resolve_gif,
    CLASS_SAVE_PROFS, SKILL_TO_STAT,
)


class Spells(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cast(self, ctx, *, args: str):
        # Turn check — only act on your turn (DMs exempt)
        from data.helpers import is_dm
        combat = self.bot.get_cog("Combat")
        if combat and combat.waiting_for_player and combat.waiting_for_player != ctx.author.id and not is_dm(ctx):
            await ctx.send("❌ It's not your turn.", delete_after=5); return
        # Rest lockout check
        conds = self.bot.get_cog("Conditions")
        if conds:
            unlock = conds._rest_lockout.get(ctx.author.id, 0)
            remaining = int(unlock - discord.utils.utcnow().timestamp())
            if remaining > 0:
                await ctx.send(f"⏳ You're still resting! Ready in **{remaining}s**."); return
        # Parse: /cast <spell> [target] [level]
        # Strategy: try spell name from longest to shortest match against CASTABLE_SPELLS
        args_lower = args.lower().strip()
        
        # Find the spell name (longest match first, must be followed by space or end)
        matched_spell = None
        remainder = ""
        for spell_key in sorted(CASTABLE_SPELLS.keys(), key=len, reverse=True):
            if args_lower == spell_key or args_lower.startswith(spell_key + " "):
                matched_spell = spell_key
                remainder = args[len(spell_key):].strip()
                break
        
        if not matched_spell:
            await ctx.send(f"❌ `{args}` not castable."); return

        # Parse remainder for target and/or upcast level
        target_name = None
        upcast_level = None
        if remainder:
            sp_check = CASTABLE_SPELLS[matched_spell]
            if sp_check["slot"] == 0:
                # Cantrip — entire remainder is the target (no upcasting)
                target_name = remainder
            else:
                # Check if last word is a number (upcast level)
                parts = remainder.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    target_name = parts[0].strip() if parts[0].strip() else None
                    upcast_level = int(parts[1])
                elif remainder.isdigit():
                    upcast_level = int(remainder)
                else:
                    target_name = remainder

        key = matched_spell
        caster = get_db_char(ctx.author.id)
        if not caster: await ctx.send("No character."); return
        sp = CASTABLE_SPELLS[key]
        from data.static_data import CLASS_SPELL_LIST
        class_spells = CLASS_SPELL_LIST.get(caster["class"], [])
        if not class_spells: await ctx.send(f"❌ {caster['class']} can't cast."); return
        if key not in class_spells: await ctx.send(f"❌ **{key.title()}** is not on the {caster['class']} spell list."); return
        # Check cast-blocking conditions
        cast_conds = [x.strip().lower() for x in (caster.get("conditions_active") or "").split(",") if x.strip()]
        if "mindnumb toxin" in cast_conds: await ctx.send("❌ **Mindnumb Toxin** — you can't cast spells!"); return
        if "curse of silence" in cast_conds: await ctx.send("❌ **Curse of Silence** — you can't cast verbal spells!"); return

        stat_key = SPELLCASTING_STAT.get(caster["class"])
        spell_mod = modifier(caster[stat_key]) if stat_key else 0
        pb = prof_bonus(caster["level"])
        spell_dc = 8 + pb + spell_mod
        spell_atk = pb + spell_mod
        # Armor passive: spell DC bonus
        from data.static_data import ARMOR_PASSIVE
        equipped_armor = caster.get("equipped_armor") or ""
        armor_passive = ARMOR_PASSIVE.get(equipped_armor, {})
        if armor_passive.get("spell_dc_bonus"):
            spell_dc += armor_passive["spell_dc_bonus"]
            spell_atk += armor_passive["spell_dc_bonus"]
        slot_level = upcast_level if upcast_level and sp["slot"] > 0 and upcast_level >= sp["slot"] else sp["slot"]
        extra_levels = max(0, slot_level - sp["slot"])

        if slot_level > 0:
            slots = get_slots(ctx.author.id)
            if not slots:
                set_slots(ctx.author.id, get_slots_for_level(caster["class"], caster["level"]))
                slots = get_slots(ctx.author.id)
            # If no slot at this level, find highest available (Warlock pact magic)
            if slots[f"slot_{slot_level}"] <= 0:
                found = None
                for i in range(slot_level, 10):
                    if slots[f"slot_{i}"] > 0:
                        found = i; break
                if not found:
                    await ctx.send(f"❌ No spell slots available."); return
                slot_level = found
                extra_levels = max(0, slot_level - sp["slot"])
            from data.db import get_db
            conn = get_db(); cur = conn.cursor()
            cur.execute(f"UPDATE spell_slots SET slot_{slot_level} = slot_{slot_level} - 1 WHERE discord_id = %s", (ctx.author.id,))
            conn.commit(); cur.close(); conn.close()

        embed = discord.Embed(title=f"✨ {caster['char_name']} casts {matched_spell.title()}!", color=discord.Color.blurple())
        is_crit = False
        from data.static_data import roll_dice_str

        if sp["cast_type"] == "attack":
            r = random.randint(1, 20)
            lucky_note = ""
            debuff_note = ""
            if r == 1 and caster and caster.get("race") == "Halfling":
                r = random.randint(1, 20)
                lucky_note = " 🍀 Lucky!"
            # Disadvantage from conditions on spell attacks
            if caster:
                p_conds = [x.strip().lower() for x in (caster.get("conditions_active") or "").split(",") if x.strip()]
                if any(c in {"poisoned", "frightened", "blinded", "restrained"} for c in p_conds):
                    r2 = random.randint(1, 20)
                    if r2 < r: r = r2
                    debuff_note = " ⚠️ (disadvantage)"
                # Buff: intellect adds +2 spell damage later, blessed adds +1d4 to attack
                buff_atk = 0
                if "buff:blessed" in p_conds: buff_atk += random.randint(1, 4)
                spell_atk += buff_atk
            is_crit = r == 20
            embed.add_field(name="Spell Attack", value=f"`{r}` +{spell_atk} = **{r+spell_atk}**" + (" 💥 CRIT!" if is_crit else "") + lucky_note + debuff_note, inline=False)
            if sp["damage"] and r != 1:
                rolls, dmg = roll_dice_str(sp["damage"])
                if is_crit: r2, d2 = roll_dice_str(sp["damage"]); rolls += r2; dmg += d2
                if extra_levels and sp["upcast"]:
                    for _ in range(extra_levels): r2, d2 = roll_dice_str(sp["upcast"]); rolls += r2; dmg += d2
                # Buff: intellect adds +2 spell damage
                if caster and "buff:intellect" in [x.strip().lower() for x in (caster.get("conditions_active") or "").split(",") if x.strip()]:
                    dmg += 2
                embed.add_field(name="Damage", value=f"`[{','.join(str(x) for x in rolls)}]` = **{dmg}**", inline=False)
        elif sp["cast_type"] == "save":
            embed.add_field(name="Save DC", value=f"**{spell_dc}** ({sp['save_stat']})", inline=False)
            if sp["damage"]:
                rolls, dmg = roll_dice_str(sp["damage"])
                if extra_levels and sp["upcast"]:
                    for _ in range(extra_levels): r2, d2 = roll_dice_str(sp["upcast"]); rolls += r2; dmg += d2
                embed.add_field(name="Damage", value=f"`[{','.join(str(x) for x in rolls)}]` = **{dmg}** (half on save: {dmg//2})", inline=False)
        elif sp["cast_type"] == "auto":
            if sp["heal"]:
                rolls, amt = roll_dice_str(sp["heal"])
                if extra_levels and sp["upcast"]:
                    for _ in range(extra_levels): r2, d2 = roll_dice_str(sp["upcast"]); rolls += r2; amt += d2
                amt += spell_mod
                embed.add_field(name="Healing", value=f"`[{','.join(str(x) for x in rolls)}]` +{spell_mod} = **{amt} HP**", inline=False)
            elif sp["damage"]:
                rolls, dmg = roll_dice_str(sp["damage"])
                if extra_levels and sp["upcast"]:
                    for _ in range(extra_levels): r2, d2 = roll_dice_str(sp["upcast"]); rolls += r2; dmg += d2
                embed.add_field(name="Effect", value=f"`[{','.join(str(x) for x in rolls)}]` = **{dmg}**", inline=False)

        base_gif = SPELL_GIF_OVERRIDE.get(key) or SCHOOL_GIF.get(sp["school"])
        gif_path = resolve_gif(base_gif, is_crit)

        # Apply damage to target enemy — auto-target random if not specified
        if sp["damage"]:
            combat = self.bot.get_cog("Combat")
            if combat:
                enemies = combat._get_enemies(ctx.guild.id)
                if not target_name and enemies:
                    target_name = random.choice(list(enemies.keys()))
        if target_name and sp["damage"]:
            combat = self.bot.get_cog("Combat")
            if combat:
                enemies = combat._get_enemies(ctx.guild.id)
                match = next((k for k in enemies if k.lower() == target_name.lower()), None)
                if not match:
                    match = next((k for k in enemies if target_name.lower() in k.lower()), None)
                if match:
                    e = enemies[match]
                    # For attack spells, check if it hit
                    if sp["cast_type"] == "attack":
                        hit_target = is_crit or (r + spell_atk) >= e["ac"]
                        if not hit_target:
                            embed.add_field(name="Target", value=f"❌ Missed **{match}** (AC {e['ac']})", inline=False)
                        else:
                            e["hp"] = max(0, e["hp"] - dmg)
                            embed.add_field(name="Target", value=f"**{match}** HP: **{e['hp']}/{e['max_hp']}**", inline=False)
                            try:
                                from data.dynamo_sync import sync_last_attack
                                sync_last_attack(ctx.author.id, match, is_crit)
                            except Exception: pass
                            if e["hp"] == 0:
                                embed.add_field(name="💀", value=f"**{match} DEFEATED!**", inline=False)
                                xp_val = e.get("xp", 0)
                                loot = e.get("loot", [])
                                session = combat.combat_sessions.get(ctx.guild.id)
                                if session:
                                    session["order"] = [(n, rv) for n, rv in session["order"] if n != f"👹 {match}"]
                                combat.combat_xp_pool[ctx.guild.id] = combat.combat_xp_pool.get(ctx.guild.id, 0) + e.get("xp", 0)
                                del enemies[match]
                                # Boss loot
                                if loot:
                                    await ctx.send(embed=embed, file=discord.File(gif_path, filename=os.path.basename(gif_path)) if gif_path else None) if gif_path else await ctx.send(embed=embed)
                                    await combat._boss_loot_rolls(ctx, loot)
                                    gif_path = None  # prevent double send
                    elif sp["cast_type"] in ("save", "auto") and sp["damage"]:
                        # Auto-hit spells (magic missile) or save spells (apply full damage, DM adjudicates saves)
                        e["hp"] = max(0, e["hp"] - dmg)
                        embed.add_field(name="Target", value=f"**{match}** HP: **{e['hp']}/{e['max_hp']}**", inline=False)
                        try:
                            from data.dynamo_sync import sync_last_attack
                            sync_last_attack(ctx.author.id, match, False)
                        except Exception: pass
                        if e["hp"] == 0:
                            embed.add_field(name="💀", value=f"**{match} DEFEATED!**", inline=False)
                            xp_val = e.get("xp", 0)
                            loot = e.get("loot", [])
                            session = combat.combat_sessions.get(ctx.guild.id)
                            if session:
                                session["order"] = [(n, rv) for n, rv in session["order"] if n != f"👹 {match}"]
                            combat.combat_xp_pool[ctx.guild.id] = combat.combat_xp_pool.get(ctx.guild.id, 0) + e.get("xp", 0)
                            del enemies[match]
                            # Boss loot
                            if loot:
                                await ctx.send(embed=embed, file=discord.File(gif_path, filename=os.path.basename(gif_path)) if gif_path else None) if gif_path else await ctx.send(embed=embed)
                                await combat._boss_loot_rolls(ctx, loot)
                                gif_path = None  # prevent double send

        if gif_path:
            embed.set_image(url=f"attachment://{os.path.basename(gif_path)}")
            await ctx.send(embed=embed, file=discord.File(gif_path, filename=os.path.basename(gif_path)))
        else:
            await ctx.send(embed=embed)

        # Apply spell effects (buffs/debuffs)
        from data.static_data import SPELL_ON_CAST_EFFECT
        effect = SPELL_ON_CAST_EFFECT.get(matched_spell)
        if effect and caster:
            if effect["type"] == "self_buff":
                conds = [x.strip() for x in (caster.get("conditions_active") or "").split(",") if x.strip()]
                buff_tag = f"buff:{effect['buff']}"
                if buff_tag not in conds:
                    conds.append(buff_tag)
                    set_char_field(ctx.author.id, "conditions_active", ", ".join(conds))
                # Apply AC bonus if any
                if effect.get("ac_bonus"):
                    set_char_field(ctx.author.id, "ac", caster.get("ac", 10) + effect["ac_bonus"])
                await ctx.send(f"⬆️ **{caster['char_name']}** gains **{effect['buff'].title().replace('_',' ')}** — *{effect['desc']}*")
            elif effect["type"] == "enemy_debuff":
                combat_cog = self.bot.get_cog("Combat")
                if combat_cog:
                    enemies = combat_cog._get_enemies(ctx.guild.id)
                    # Apply to the target enemy (if one was specified in the cast)
                    if target_name and enemies:
                        match = next((k for k in enemies if target_name.lower() in k.lower()), None)
                        if match:
                            e = enemies[match]
                            if "active_conditions" not in e:
                                e["active_conditions"] = []
                            e["active_conditions"].append({"name": effect["condition"], "expires_in": 99})
                            await ctx.send(f"⬇️ **{match}** is **{effect['condition'].upper()}** — *{effect['desc']}*")
                        else:
                            await ctx.send(f"⬇️ *{effect['desc']}* (DM: apply to target)")
                    else:
                        await ctx.send(f"⬇️ *{effect['desc']}* (DM: apply to target)")

        # Auto-advance combat if it's this player's turn
        combat = self.bot.get_cog("Combat")
        if combat and combat.waiting_for_player == ctx.author.id:
            combat._cancel_timer()
            # Check if all enemies are dead — auto-end combat
            if not combat._get_enemies(ctx.guild.id):
                await combat._auto_end_combat(ctx)
            else:
                await combat._advance_turn(ctx)

    @commands.command()
    async def spellslots(self, ctx):
        slots = get_slots(ctx.author.id)
        if not slots: await ctx.send("No spell slots."); return
        lines = [f"**Level {i}:** {slots[f'slot_{i}']}" for i in range(1,10) if slots[f"slot_{i}"] > 0]
        if not lines: await ctx.send("No spell slots."); return
        embed = discord.Embed(title="🔮 Spell Slots", color=discord.Color.blurple())
        embed.description = "\n".join(lines)
        await dm_reply(ctx, embed=embed)

    @commands.command()
    async def spelldc(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        stat_key = SPELLCASTING_STAT.get(c["class"])
        if not stat_key: await ctx.send("Not a caster."); return
        pb = prof_bonus(c["level"]); mod = modifier(c[stat_key])
        await ctx.send(f"🔮 Spell DC: **{8+pb+mod}** | Attack: **+{pb+mod}**")

    @commands.command()
    async def spell(self, ctx, *, name: str):
        key = name.lower()
        if key not in SPELLS: await ctx.send("❌ Not found."); return
        level, school, range_, desc = SPELLS[key]
        embed = discord.Embed(title=f"✨ {name.title()}", color=discord.Color.blurple())
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="School", value=school, inline=True)
        embed.add_field(name="Range", value=range_, inline=True)
        embed.add_field(name="Description", value=desc, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def concentrate(self, ctx, *, spell_name: str):
        c = get_db_char(ctx.author.id)
        if not c: return
        set_char_field(ctx.author.id, "concentration", spell_name)
        await ctx.send(f"🔮 **{c['char_name']}** concentrating on **{spell_name}**.")

    @commands.command()
    async def endconcentration(self, ctx):
        set_char_field(ctx.author.id, "concentration", None)
        await ctx.send("✅ Concentration ended.")

    @commands.command()
    async def learnspell(self, ctx, *, spell_name: str):
        if spell_name.lower() not in SPELLS: await ctx.send("❌ Not found."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        # Check class spell list
        from data.static_data import CLASS_SPELL_LIST
        class_spells = CLASS_SPELL_LIST.get(c["class"], [])
        if class_spells and spell_name.lower() not in class_spells:
            await ctx.send(f"❌ **{spell_name.title()}** is not on the {c['class']} spell list."); return
        # Check if it's a cantrip (unlimited)
        spell_level = SPELLS[spell_name.lower()][0]
        known = [s.strip() for s in (c.get("known_spells") or "").split(",") if s.strip()]
        if spell_name.lower() in known: await ctx.send("Already known."); return
        # Enforce cap for non-cantrip spells
        if spell_level != "Cantrip":
            from data.static_data import get_max_known_spells, modifier as _mod
            non_cantrips = [s for s in known if s in SPELLS and SPELLS[s][0] != "Cantrip"]
            max_known = get_max_known_spells(
                c["class"], c["level"],
                int_mod=_mod(c["intelligence"]),
                wis_mod=_mod(c["wisdom"]),
                cha_mod=_mod(c["charisma"])
            )
            if len(non_cantrips) >= max_known:
                await ctx.send(f"❌ **{c['char_name']}** already knows **{len(non_cantrips)}/{max_known}** spells (max for {c['class']} level {c['level']}). Use `!forgotspell <name>` to make room.")
                return
        known.append(spell_name.lower())
        set_char_field(ctx.author.id, "known_spells", ", ".join(known))
        await ctx.send(f"📖 **{c['char_name']}** learned **{spell_name.title()}**!")

    @commands.command()
    async def spellbook(self, ctx):
        """View all spells available to your class with level availability."""
        c = get_db_char(ctx.author.id)
        if not c: await ctx.send("No character found."); return
        from data.static_data import CLASS_SPELL_LIST
        class_spells = CLASS_SPELL_LIST.get(c["class"], [])
        if not class_spells: await ctx.send(f"❌ **{c['class']}** cannot cast spells."); return

        # Get known spell count and cap
        from data.static_data import get_max_known_spells, modifier as _mod, get_slots_for_level as _gsfl
        known = [s.strip() for s in (c.get("known_spells") or "").split(",") if s.strip()]
        non_cantrips_known = [s for s in known if s in SPELLS and SPELLS[s][0] != "Cantrip"]
        max_known = get_max_known_spells(c["class"], c["level"], _mod(c["intelligence"]), _mod(c["wisdom"]), _mod(c["charisma"]))

        # Get current slots to determine what levels are available
        slots = _gsfl(c["class"], c["level"])
        # Slot index 0 = level 1, index 1 = level 2, etc.

        # Map spell level strings to slot index
        level_to_index = {"1st":0, "2nd":1, "3rd":2, "4th":3, "5th":4, "6th":5, "7th":6, "8th":7, "9th":8}

        # Filter spells by class spell list
        available = {}
        for spell_name, (level, school, range_, desc) in SPELLS.items():
            if spell_name in class_spells:
                available.setdefault(level, []).append(spell_name.title())

        if not available: await ctx.send("No spells available."); return

        cap_str = f"∞" if max_known >= 999 else f"{len(non_cantrips_known)}/{max_known}"
        embed = discord.Embed(
            title=f"📖 {c['char_name']}'s Spellbook — {c['class']} (Level {c['level']})",
            description=f"**Known spells:** {cap_str}",
            color=discord.Color.blurple()
        )

        for lvl in ["Cantrip","1st","2nd","3rd","4th","5th","6th","7th","8th","9th"]:
            if lvl not in available:
                continue
            spells_list = sorted(available[lvl])
            if lvl == "Cantrip":
                label = "✅ Cantrip (free — learn any)"
                value = ", ".join(spells_list)
            else:
                idx = level_to_index.get(lvl, 99)
                has_slots = idx < len(slots) and slots[idx] > 0
                # Warlocks can cast lower-level spells with their higher-level pact slots
                if not has_slots and any(slots[i] > 0 for i in range(idx, len(slots))):
                    has_slots = True
                if has_slots:
                    label = f"✅ {lvl} (you have slots)"
                    value = ", ".join(spells_list)
                else:
                    label = f"🔒 {lvl} (not yet)"
                    value = "~~" + ", ".join(spells_list) + "~~"
            embed.add_field(name=label, value=value, inline=False)

        embed.set_footer(text="Use /learnspell <name> to learn. Cantrips are free. Non-cantrips count toward your limit.")
        embed.set_image(url="attachment://spellbook.gif")
        await dm_reply(ctx, embed=embed, file=discord.File("vfx/entity_vfx/spellbook.gif", filename="spellbook.gif"))

    @commands.command()
    async def myspells(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        known = [s.strip() for s in (c.get("known_spells") or "").split(",") if s.strip()]
        if not known: await ctx.send("No known spells."); return
        embed = discord.Embed(title=f"📖 {c['char_name']}'s Spells", color=discord.Color.blurple())
        embed.description = ", ".join(s.title() for s in known)
        await ctx.send(embed=embed)

    @commands.command()
    async def useslot(self, ctx, level: int):
        if not 1 <= level <= 9: return
        slots = get_slots(ctx.author.id)
        if not slots or slots[f"slot_{level}"] <= 0: await ctx.send(f"❌ No level {level} slots."); return
        from data.db import get_db
        conn = get_db(); cur = conn.cursor()
        cur.execute(f"UPDATE spell_slots SET slot_{level} = slot_{level} - 1 WHERE discord_id = %s", (ctx.author.id,))
        conn.commit(); cur.close(); conn.close()
        await ctx.send(f"🔮 Level {level} slot used. Remaining: **{slots[f'slot_{level}']-1}**")


async def setup(bot):
    await bot.add_cog(Spells(bot))
