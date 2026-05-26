import random
import discord
from discord.ext import commands

from _config import DREAD_SECRET_THRESHOLD
from data.db import get_db_char, set_char_field, load_active_characters, get_db, set_slots
from data.helpers import dm_reply
from data.static_data import (
    CONDITIONS, EXHAUSTION_EFFECTS, SKILL_TO_STAT, STAT_FOR_SAVE,
    CLASS_SAVE_PROFS, modifier, mod_str, prof_bonus, get_slots_for_level,
    RACIAL_ABILITIES, DRAGONBORN_ANCESTRY, get_breath_damage,
)


class Conditions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._rest_lockout = {}  # {user_id: unlock_timestamp}

    async def maybe_secret_roll(self, ctx, c, result_msg):
        dread = c.get("dread", 0) or 0
        if dread < DREAD_SECRET_THRESHOLD:
            return False
        await ctx.send(f"🎲 **{c['char_name']}** rolls... 👁️ *The house obscures the result.*")
        # Find DM and send privately
        dm_member = None
        for member in ctx.guild.members:
            if any(r.name.lower() in ("dm","dungeon master","game master","gm") for r in member.roles):
                dm_member = member; break
        if dm_member:
            try:
                dm_channel = await dm_member.create_dm()
                embed = discord.Embed(title=f"🎲 Secret Roll — {c['char_name']}", description=result_msg, color=discord.Color.dark_purple())
                embed.set_footer(text=f"Dread {dread} — announce whatever you want.")
                await dm_channel.send(embed=embed)
            except: pass
        return True

    # ── Saves & Checks ─────────────────────────────────────────────────────────

    @commands.command()
    async def save(self, ctx, *, stat: str):
        key = stat.lower()
        if key not in STAT_FOR_SAVE: await ctx.send("❌ Use: str/dex/con/int/wis/cha"); return
        c = get_db_char(ctx.author.id)
        if not c: return
        stat_key = STAT_FOR_SAVE[key]
        r = random.randint(1, 20)
        lucky_note = ""
        if r == 1 and c.get("race") == "Halfling":
            r = random.randint(1, 20)
            lucky_note = " 🍀 Lucky!"
        base = modifier(c[stat_key])
        save_profs = CLASS_SAVE_PROFS.get(c["class"], set())
        pb = prof_bonus(c["level"]) if stat_key in save_profs else 0
        total = r + base + pb
        # Buff bonuses on saves
        p_conds = [x.strip().lower() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        if "buff:blessed" in p_conds: total += random.randint(1, 4)
        if f"buff:{stat_key}" in p_conds: total += 2
        # Disease/poison penalties
        if "void sickness" in p_conds: total -= 1
        if "creeping rot" in p_conds and stat_key == "constitution": total -= 2
        # Dread 3+: disadvantage on Wisdom saves
        dread = c.get("dread", 0) or 0
        if dread >= 3 and stat_key == "wisdom":
            r2 = random.randint(1, 20)
            if r2 < r: total = r2 + base + pb
        # Disadvantage on specific saves
        if "blackhollow spores" in p_conds and stat_key == "wisdom":
            r2 = random.randint(1, 20)
            if r2 < r: total = r2 + base + pb
        prof_note = f" +{pb} (prof)" if pb else ""
        crit = " 💥 Nat 20!" if r == 20 else (" 💀 Nat 1!" if r == 1 else "")
        result_msg = f"{stat_key.title()} save: `{r}` {mod_str(c[stat_key])}{prof_note} = **{total}**{crit}{lucky_note}"
        if await self.maybe_secret_roll(ctx, c, result_msg): return
        await ctx.send(f"🎲 **{ctx.author.display_name}** {result_msg}")
        # Auto-advance combat
        combat = self.bot.get_cog("Combat")
        if combat and combat.waiting_for_player == ctx.author.id:
            combat._cancel_timer()
            await combat._advance_turn(ctx)

    @commands.command()
    async def check(self, ctx, *, skill: str):
        key = skill.lower()
        if key not in SKILL_TO_STAT: await ctx.send("❌ Unknown skill."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        stat_key = SKILL_TO_STAT[key]
        skill_profs = [s.strip().lower() for s in (c.get("skill_profs") or "").split(",") if s.strip()]
        expertise = [s.strip().lower() for s in (c.get("expertise") or "").split(",") if s.strip()]
        pb = prof_bonus(c["level"])
        if key in expertise: bonus = pb * 2; prof_note = f" +{pb*2} (expertise)"
        elif key in skill_profs: bonus = pb; prof_note = f" +{pb} (prof)"
        else: bonus = 0; prof_note = ""
        r = random.randint(1, 20)
        lucky_note = ""
        if r == 1 and c.get("race") == "Halfling":
            r = random.randint(1, 20)
            lucky_note = " 🍀 Lucky!"
        # Debuff/buff on checks
        p_conds = [x.strip().lower() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        # Dread 1+: disadvantage on Investigation inside the house
        dread = c.get("dread", 0) or 0
        if dread >= 1 and key == "investigation":
            r2 = random.randint(1, 20)
            if r2 < r: r = r2
        if "creeping madness" in p_conds and stat_key in ("intelligence", "wisdom"):
            r2 = random.randint(1, 20)
            if r2 < r: r = r2
        if "buff:inspired" in p_conds:
            r2 = random.randint(1, 20)
            if r2 > r: r = r2
            p_conds.remove("buff:inspired")
            set_char_field(ctx.author.id, "conditions_active", ", ".join(p_conds) if p_conds else None)
        total = r + modifier(c[stat_key]) + bonus
        crit = " 💥 Nat 20!" if r == 20 else (" 💀 Nat 1!" if r == 1 else "")
        result_msg = f"{key.title()}: `{r}` {mod_str(c[stat_key])}{prof_note} = **{total}**{crit}{lucky_note}"
        if await self.maybe_secret_roll(ctx, c, result_msg): return
        await ctx.send(f"🎲 **{ctx.author.display_name}** {result_msg}")

    @commands.command()
    async def roll(self, ctx, dice: str = "1d20"):
        dice = dice.lower()
        if dice == "advantage":
            r1, r2 = random.randint(1,20), random.randint(1,20)
            await ctx.send(f"🎲 **Advantage:** `{r1}` and `{r2}` → **{max(r1,r2)}**"); return
        if dice == "disadvantage":
            r1, r2 = random.randint(1,20), random.randint(1,20)
            await ctx.send(f"🎲 **Disadvantage:** `{r1}` and `{r2}` → **{min(r1,r2)}**"); return
        try:
            count, sides = dice.split("d")
            count, sides = int(count), int(sides)
        except: await ctx.send("❌ Use NdX (e.g. 2d6)"); return
        rolls = [random.randint(1, sides) for _ in range(count)]
        await ctx.send(f"🎲 **{dice.upper()}:** `[{', '.join(str(r) for r in rolls)}]` → **{sum(rolls)}**")

    # ── Conditions ─────────────────────────────────────────────────────────────

    @commands.command()
    async def condition(self, ctx, *, name: str):
        if name.lower() not in CONDITIONS: await ctx.send("❌ Unknown."); return
        embed = discord.Embed(title=f"🩸 {name.title()}", description=CONDITIONS[name.lower()], color=discord.Color.dark_red())
        await ctx.send(embed=embed)

    @commands.command()
    async def conditions(self, ctx):
        embed = discord.Embed(title="🩸 Conditions", color=discord.Color.dark_red())
        embed.description = "\n".join(f"**{k.title()}**" for k in CONDITIONS.keys())
        await ctx.send(embed=embed)

    @commands.command()
    async def applycondition(self, ctx, *, condition_name: str):
        if condition_name.lower() not in CONDITIONS: await ctx.send("❌ Unknown."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        existing = [x for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        if condition_name.lower() not in existing: existing.append(condition_name.lower())
        set_char_field(ctx.author.id, "conditions_active", ", ".join(existing))
        await ctx.send(f"🩸 **{c['char_name']}** is now **{condition_name}**.")

    @commands.command()
    async def removecondition(self, ctx, *, condition_name: str):
        c = get_db_char(ctx.author.id)
        if not c: return
        existing = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        if condition_name.lower() in existing: existing.remove(condition_name.lower())
        set_char_field(ctx.author.id, "conditions_active", ", ".join(existing) if existing else None)
        await ctx.send(f"✅ **{condition_name}** removed.")

    # ── Exhaustion ─────────────────────────────────────────────────────────────

    @commands.command()
    async def exhaustion(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        level = c.get("exhaustion", 0) or 0
        if level == 0: await ctx.send(f"✅ **{c['char_name']}** has no exhaustion."); return
        embed = discord.Embed(title=f"😰 {c['char_name']} — Exhaustion Level {level}", color=discord.Color.dark_orange())
        for i in range(1, level + 1):
            embed.add_field(name=f"Level {i}", value=EXHAUSTION_EFFECTS[i], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def exhaust(self, ctx, levels: int = 1):
        c = get_db_char(ctx.author.id)
        if not c: return
        new_val = min(6, (c.get("exhaustion", 0) or 0) + levels)
        set_char_field(ctx.author.id, "exhaustion", new_val)
        await ctx.send(f"😰 **{c['char_name']}** exhaustion: **{new_val}** — {EXHAUSTION_EFFECTS.get(new_val,'')}")

    # ── HP ─────────────────────────────────────────────────────────────────────

    @commands.command()
    async def hp(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        await ctx.send(f"❤️ **{c['char_name']}** HP: **{c['hp']}** / {c.get('max_hp') or c['hp']}")

    @commands.command()
    async def heal(self, ctx, amount: int):
        c = get_db_char(ctx.author.id)
        if not c: return
        max_hp = c.get("max_hp") or c["hp"]
        new_hp = min(max_hp, c["hp"] + amount)
        set_char_field(ctx.author.id, "hp", new_hp)
        await ctx.send(f"💚 **{c['char_name']}** heals **{amount}**. HP: **{new_hp}/{max_hp}**")

    @commands.command()
    async def takedamage(self, ctx, amount: int):
        c = get_db_char(ctx.author.id)
        if not c: return
        temp = c.get("temp_hp", 0) or 0
        remaining = amount
        if temp > 0:
            absorbed = min(temp, remaining); remaining -= absorbed
            set_char_field(ctx.author.id, "temp_hp", temp - absorbed)
        new_hp = max(0, c["hp"] - remaining)
        set_char_field(ctx.author.id, "hp", new_hp)
        max_hp = c.get("max_hp") or c["hp"]
        msg = f"💥 **{c['char_name']}** takes **{amount}** damage. HP: **{new_hp}/{max_hp}**"
        if new_hp == 0: msg += " 💀 **DOWN!**"
        await ctx.send(msg)

    @commands.command()
    async def temphp(self, ctx, amount: int):
        c = get_db_char(ctx.author.id)
        if not c: return
        set_char_field(ctx.author.id, "temp_hp", max(c.get("temp_hp",0) or 0, amount))
        await ctx.send(f"🛡️ Temp HP set to **{amount}**.")

    @commands.command()
    async def shortrest(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        # Charge check: max 2 short rests per long rest
        used = c.get("short_rest_used", 0) or 0
        if used >= 2:
            await ctx.send("❌ No short rests remaining. Take a long rest to reset."); return
        from data.static_data import CLASS_HP
        hit_die = CLASS_HP.get(c["class"], 8)
        remaining = c.get("hit_dice_remaining") or 0
        if remaining <= 0: await ctx.send("❌ No hit dice remaining."); return
        roll_result = random.randint(1, hit_die)
        heal_amt = max(1, roll_result + modifier(c["constitution"]))
        max_hp = c.get("max_hp") or c["hp"]
        new_hp = min(max_hp, c["hp"] + heal_amt)
        from data.db import get_db
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE characters SET hp=%s, hit_dice_remaining=%s WHERE discord_id=%s", (new_hp, remaining-1, ctx.author.id))
        conn.commit(); cur.close(); conn.close()
        set_char_field(ctx.author.id, "short_rest_used", used + 1)
        # Combat lockout 15s
        self._rest_lockout[ctx.author.id] = discord.utils.utcnow().timestamp() + 15
        # Clear minor conditions on short rest (poisoned, frightened, charmed)
        conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        minor_conds = {"poisoned", "frightened", "charmed", "prone", "weak venom", "blinded", "deafened"}
        cleared = [x for x in conds if x.lower() in minor_conds]
        if cleared:
            remaining_conds = [x for x in conds if x.lower() not in minor_conds]
            set_char_field(ctx.author.id, "conditions_active", ", ".join(remaining_conds) if remaining_conds else None)
        cleared_msg = f"\n✨ Cleared: {', '.join(c.title() for c in cleared)}" if cleared else ""
        await ctx.send(f"🌗 **{c['char_name']}** short rest. +**{heal_amt} HP** → {new_hp}/{max_hp}. Hit dice: {remaining-1}/{c['level']}.\n⏳ Locked out of combat for **15s**. Rests: {2 - used - 1}/2 remaining.{cleared_msg}")
        # Reset short-rest racial abilities (Dragonborn Breath Weapon)
        ability = RACIAL_ABILITIES.get(c.get("race", ""))
        if ability and ability.get("recharge") == "short_rest":
            set_char_field(ctx.author.id, "racial_uses", 0)

    @commands.command()
    async def longrest(self, ctx):
        """Players cannot long rest on their own. DM controls this."""
        await ctx.send("❌ Long rests are controlled by the DM. Ask your DM when it's time to rest.")

    @commands.command()
    async def deathsave(self, ctx):
        r = random.randint(1, 20)
        if r == 20: result = "💖 **Critical Success!** Regain 1 HP!"
        elif r >= 10: result = f"✅ **Success** ({r})"
        elif r == 1: result = "💀 **Critical Failure!** Two failures."
        else: result = f"❌ **Failure** ({r})"
        await ctx.send(f"🎲 **{ctx.author.display_name}** death save: {result}")

    @commands.command()
    async def passive(self, ctx, skill: str = "perception"):
        c = get_db_char(ctx.author.id)
        if not c: return
        stat_key = SKILL_TO_STAT.get(skill.lower(), "wisdom")
        score = 10 + modifier(c[stat_key]) + prof_bonus(c["level"])
        await ctx.send(f"👁️ Passive {skill.title()}: **{score}**")

    @commands.command()
    async def racial(self, ctx, *, target_name: str = ""):
        """Use your racial ability."""
        c = get_db_char(ctx.author.id)
        if not c:
            await ctx.send("No character found."); return
        race = c.get("race", "")
        ability = RACIAL_ABILITIES.get(race)
        if not ability:
            await ctx.send(f"❌ {race} has no active racial ability."); return

        # Check uses
        if ability["uses"] > 0:
            used = c.get("racial_uses", 0)
            if used >= ability["uses"]:
                await ctx.send(f"❌ **{ability['name']}** already used. Recharges on {ability['recharge'].replace('_', ' ')}."); return

        ab_type = ability["type"]

        if ab_type == "passive" or ab_type == "passive_trigger":
            await ctx.send(f"ℹ️ **{ability['name']}** is passive — it activates automatically."); return

        if ab_type == "reroll":
            # Human Determination — just mark as used, DM handles narratively
            set_char_field(ctx.author.id, "racial_uses", c.get("racial_uses", 0) + 1)
            await ctx.send(f"🎲 **{c['char_name']}** uses **{ability['name']}!** Reroll one failed ability check."); return

        # Damage abilities
        if ab_type in ("damage_aoe", "damage_single"):
            level = c["level"]
            # Determine damage dice
            dmg_dice = ability["damage"]
            for lvl_req in sorted(ability.get("scaling", {}).keys(), reverse=True):
                if level >= lvl_req:
                    dmg_dice = ability["scaling"][lvl_req]; break

            # Dragonborn ancestry override
            damage_type = ability["damage_type"]
            save_stat = ability["save_stat"]
            if race == "Dragonborn":
                ancestry = c.get("dragon_ancestry", "Red")
                anc = DRAGONBORN_ANCESTRY.get(ancestry, {})
                damage_type = anc.get("damage_type", "fire")
                save_stat = anc.get("save_stat", "dexterity")
                dmg_dice = get_breath_damage(level)

            # Calculate save DC
            dc_formula = ability["save_dc"]
            if "CON" in dc_formula:
                dc = 8 + modifier(c["constitution"]) + prof_bonus(level)
            elif "CHA" in dc_formula:
                dc = 8 + modifier(c["charisma"]) + prof_bonus(level)
            else:
                dc = 8 + prof_bonus(level)

            # Roll damage
            num, sides = dmg_dice.split("d")
            rolls = [random.randint(1, int(sides)) for _ in range(int(num))]
            total_dmg = sum(rolls)

            # Apply to enemies
            combat = self.bot.get_cog("Combat")
            if not combat:
                await ctx.send(f"❌ No active combat."); return
            enemies = combat._get_enemies(ctx.guild.id)
            if not enemies:
                await ctx.send(f"❌ No enemies to target."); return

            msg = f"🐉 **{c['char_name']}** uses **{ability['name']}!** ({damage_type.title()})\n"
            msg += f"💥 Damage: `[{', '.join(str(r) for r in rolls)}]` = **{total_dmg}**\n"
            msg += f"DC {dc} {save_stat.upper()} save:\n"

            if ab_type == "damage_aoe":
                targets = list(enemies.items())
            else:
                # Single target
                if not target_name:
                    target_name = random.choice(list(enemies.keys()))
                match = next((k for k in enemies if k.lower() == target_name.lower()), None)
                if not match:
                    match = next((k for k in enemies if target_name.lower() in k.lower()), None)
                if not match:
                    await ctx.send(f"❌ No enemy named `{target_name}`."); return
                targets = [(match, enemies[match])]

            for ename, e in targets:
                save_roll = random.randint(1, 20) + modifier(e.get("stats", {}).get(save_stat[:3], 10))
                if save_roll >= dc:
                    half = total_dmg // 2
                    e["hp"] = max(0, e["hp"] - half)
                    msg += f"  ✅ {ename}: saves ({save_roll}) — {half} dmg → HP: {e['hp']}/{e['max_hp']}\n"
                else:
                    e["hp"] = max(0, e["hp"] - total_dmg)
                    msg += f"  ❌ {ename}: fails ({save_roll}) — {total_dmg} dmg → HP: {e['hp']}/{e['max_hp']}\n"
                if e["hp"] == 0:
                    msg += f"  💀 **{ename} is DEFEATED!**\n"
                    session = combat.combat_sessions.get(ctx.guild.id)
                    if session:
                        session["order"] = [(n, r) for n, r in session["order"] if n != f"👹 {ename}"]
                    combat.combat_xp_pool[ctx.guild.id] = combat.combat_xp_pool.get(ctx.guild.id, 0) + e.get("xp", 0)
                    del enemies[ename]

            # Mark used
            if ability["uses"] > 0:
                set_char_field(ctx.author.id, "racial_uses", c.get("racial_uses", 0) + 1)

            await ctx.send(msg)
            # Check auto-end
            if not enemies:
                await combat._auto_end_combat(ctx)

    @commands.command()
    async def racialinfo(self, ctx):
        """View your racial ability."""
        c = get_db_char(ctx.author.id)
        if not c:
            await ctx.send("No character found."); return
        race = c.get("race", "")
        ability = RACIAL_ABILITIES.get(race)
        if not ability:
            await ctx.send(f"ℹ️ {race} has no special racial ability defined."); return
        used = c.get("racial_uses", 0)
        remaining = "∞" if ability["uses"] == -1 else str(max(0, ability["uses"] - used))
        recharge = ability["recharge"].replace("_", " ") if ability["recharge"] != "none" else "always active"
        embed = discord.Embed(title=f"🧬 {ability['name']} ({race})", color=discord.Color.teal())
        embed.add_field(name="Effect", value=ability["description"], inline=False)
        embed.add_field(name="Uses", value=f"{remaining} remaining", inline=True)
        embed.add_field(name="Recharge", value=recharge.title(), inline=True)
        if "damage" in ability:
            level = c["level"]
            dmg = ability["damage"]
            for lvl_req in sorted(ability.get("scaling", {}).keys(), reverse=True):
                if level >= lvl_req:
                    dmg = ability["scaling"][lvl_req]; break
            if race == "Dragonborn":
                dmg = get_breath_damage(level)
                ancestry = c.get("dragon_ancestry", "Red")
                embed.add_field(name="Ancestry", value=ancestry, inline=True)
            embed.add_field(name="Damage", value=dmg, inline=True)
        await dm_reply(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Conditions(bot))
