import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

import sys
sys.path.insert(0, '..')
from _config import COMBAT_TURN_TIMER, XP_MODE, ACTIVE_PLAYERS
from data.db import get_db_char, set_char_field, load_active_characters
from data.static_data import (
    ENEMY_ATTACK_STATS, HOSTILE_MENAGERIE, COMMON_LOOT_TABLE,
    CLASS_HP, modifier, mod_str, prof_bonus, get_slots_for_level,
    CLASS_FEATURES, WEAPONS, SNEAK_ATTACK_DICE, roll_dice_str,
    get_weapon_proficiencies, CAMPAIGN_WEAPONS, WEAPON_RARITY,
    CLASS_SAVE_PROFS, XP_THRESHOLDS,
    ENEMY_ATTACK_FLAVOR, DEFAULT_ATTACK_FLAVOR, PLAYER_MISS_FLAVOR, PLAYER_CRIT_FLAVOR,
    STEWARD_COMBAT_START, STEWARD_COMBAT_END, STEWARD_TPK, STEWARD_LEVEL_UP,
    ENEMY_SPAWN_GIF, get_weapon_gif, resolve_gif,
    TURN_SKIP_CONDITIONS, DOT_CONDITIONS, BOSS_CONDITION_IMMUNITIES,
    WEAPON_ON_CRIT, WEAPON_ON_HIT, CONDITION_DEFAULTS,
    get_player_condition_resistance, ENEMY_ON_HIT_CONDITION,
    CAMPAIGN_ARMOR, CLASS_ARMOR_PROF, LIGHT_ARMOR, MEDIUM_ARMOR, HEAVY_ARMOR,
    CLASS_WEAPON_PROF, ARMOR_RARITY,
)


class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.combat_sessions = {}   # guild_id -> {"order": [], "turn": int}
        self.enemy_roster = {}      # guild_id -> {name: {hp, max_hp, ac, ...}}
        self.reaction_used = {}     # guild_id -> set of discord_ids
        self.turn_task = None       # asyncio task for auto-advance timer
        self.waiting_for_player = None  # discord_id of player whose turn it is
        self.combat_xp_pool = {}    # guild_id -> total XP earned this combat
        self.condition_durations = {}  # guild_id -> {discord_id: {condition: turns_left}}

    def _get_enemies(self, guild_id):
        return self.enemy_roster.setdefault(guild_id, {})

    def get_active_player_count(self):
        if ACTIVE_PLAYERS > 0:
            return ACTIVE_PLAYERS
        return len(load_active_characters()) or 1

    # ── Auto-Advance System ────────────────────────────────────────────────────

    async def _start_turn_timer(self, ctx, player_name):
        """Start a timer. If player doesn't act within COMBAT_TURN_TIMER seconds, auto-Dodge."""
        try:
            await asyncio.sleep(COMBAT_TURN_TIMER)
            # Timer expired — player didn't act
            from data.static_data import STEWARD_DODGE_TIMEOUT
            await ctx.send(f"⏰ **{player_name}** didn't act in {COMBAT_TURN_TIMER}s — taking the **Dodge** action.")
            await ctx.send(random.choice(STEWARD_DODGE_TIMEOUT))
            self.waiting_for_player = None
            await self._advance_turn(ctx)
        except asyncio.CancelledError:
            pass  # Timer was cancelled because player acted

    def _cancel_timer(self):
        """Cancel the turn timer (player acted)."""
        if self.turn_task and not self.turn_task.done():
            self.turn_task.cancel()
        self.turn_task = None
        self.waiting_for_player = None
        self.condition_durations.pop(ctx.guild.id, None)

    async def _advance_turn(self, ctx):
        """Advance through enemy turns until a player turn, then start timer."""
        session = self.combat_sessions.get(ctx.guild.id)
        if not session or not session["order"]:
            return

        # Tick down buff durations for the player who just acted
        if self.waiting_for_player:
            from data.static_data import BUFFS
            pc = get_db_char(self.waiting_for_player)
            if pc:
                conds = [x.strip() for x in (pc.get("conditions_active") or "").split(",") if x.strip()]
                expired = []
                for cond in conds:
                    if cond.startswith("buff:"):
                        buff_key = cond[5:]
                        b = BUFFS.get(buff_key)
                        if b and b["duration"] > 0:
                            # Track in memory (simple: decrement a counter dict)
                            dur_key = (self.waiting_for_player, buff_key)
                            self._buff_durations = getattr(self, "_buff_durations", {})
                            self._buff_durations[dur_key] = self._buff_durations.get(dur_key, b["duration"]) - 1
                            if self._buff_durations[dur_key] <= 0:
                                expired.append(cond)
                                # Reverse AC if needed
                                if "ac_plus_2" in b["mechanical"]:
                                    set_char_field(pc["discord_id"], "ac", max(1, pc.get("ac", 10) - 2))
                                del self._buff_durations[dur_key]
                if expired:
                    new_conds = [c for c in conds if c not in expired]
                    set_char_field(pc["discord_id"], "conditions_active", ", ".join(new_conds) if new_conds else None)
                    names = ", ".join(c[5:].title() for c in expired)
                    await ctx.send(f"⏳ **{pc['char_name']}** — **{names}** expired.")

        # Safety: if no players in order, don't loop
        has_player = any(not name.startswith("👹") for name, _ in session["order"])
        if not has_player:
            await ctx.send("⚠️ No players in combat. Use `!endcombat` to stop.")
            return

        max_iterations = len(session["order"]) * 2
        iterations = 0
        enemy_log = []

        while True:
            iterations += 1
            if iterations > max_iterations:
                await ctx.send("⚠️ Combat loop detected. Ending.")
                self.combat_sessions.pop(ctx.guild.id, None)
                return
            if ctx.guild.id not in self.combat_sessions:
                return

            session["turn"] = (session["turn"] + 1) % len(session["order"])
            current = session["order"][session["turn"]][0]

            if current.startswith("👹"):
                enemy_name = current[2:]
                enemies = self._get_enemies(ctx.guild.id)
                enemy = enemies.get(enemy_name)
                if enemy:
                    # Check conditions — skip turn if stunned/paralyzed
                    active_conds = enemy.get("active_conditions", [])
                    skip = False
                    for cond in active_conds:
                        if cond["name"] in TURN_SKIP_CONDITIONS:
                            enemy_log.append(f"👹 **{enemy_name}** — 💫 **{cond['name'].upper()}**. Turn skipped.")
                            skip = True
                            break
                    # Apply DOT damage
                    for cond in active_conds:
                        if cond["name"] in DOT_CONDITIONS:
                            dice, dmg_type = DOT_CONDITIONS[cond["name"]]
                            dot_rolls, dot_dmg = roll_dice_str(dice)
                            enemy["hp"] = max(0, enemy["hp"] - dot_dmg)
                            enemy_log.append(f"🔥 **{enemy_name}** takes **{dot_dmg} {dmg_type}** from {cond['name']}. HP: {enemy['hp']}/{enemy['max_hp']}")
                            if enemy["hp"] == 0:
                                enemy_log.append(f"💀 **{enemy_name} DEFEATED** by {cond['name']}!")
                                self.combat_xp_pool[ctx.guild.id] = self.combat_xp_pool.get(ctx.guild.id, 0) + enemy.get("xp", 0)
                                session = self.combat_sessions.get(ctx.guild.id)
                                if session:
                                    session["order"] = [(n, rv) for n, rv in session["order"] if n != f"👹 {enemy_name}"]
                                del enemies[enemy_name]
                                skip = True
                                break
                    # Decrement condition durations
                    if not skip:
                        enemy["active_conditions"] = [c for c in active_conds if c.update({"expires_in": c["expires_in"] - 1}) or c["expires_in"] > 0]
                    else:
                        # Still decrement even if skipped
                        enemy_remaining = enemies.get(enemy_name)
                        if enemy_remaining:
                            enemy_remaining["active_conditions"] = [c for c in active_conds if c.update({"expires_in": c["expires_in"] - 1}) or c["expires_in"] > 0]
                        continue
                    # Enemy regeneration
                    regen = enemy.get("regen", 0)
                    if regen and enemy["hp"] < enemy["max_hp"]:
                        enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + regen)
                        enemy_log.append(f"💚 **{enemy_name}** regenerates **{regen} HP** → {enemy['hp']}/{enemy['max_hp']}")
                    result = await self._auto_enemy_attack_silent(ctx, enemy_name, enemy)
                    enemy_log.append(result)
                    if not self._get_enemies(ctx.guild.id):
                        if enemy_log:
                            await self._send_enemy_phase_embed(ctx, enemy_log)
                        await self._auto_end_combat(ctx)
                        return
                    alive = [c for c in load_active_characters() if c["hp"] > 0]
                    if not alive:
                        enemy_log.append("💀 **TOTAL PARTY KILL.** The house claims you.")
                        enemy_log.append(random.choice(STEWARD_TPK))
                        await self._send_enemy_phase_embed(ctx, enemy_log)
                        self.combat_sessions.pop(ctx.guild.id, None)
                        return
                else:
                    continue
            else:
                if enemy_log:
                    await self._send_enemy_phase_embed(ctx, enemy_log)
                    enemy_log = []
                chars = load_active_characters()
                player_char = next((c for c in chars if c["char_name"] == current), None)
                if player_char and player_char["hp"] <= 0:
                    continue

                alive = [c for c in chars if c["hp"] > 0]
                if not alive:
                    await ctx.send("💀 **TOTAL PARTY KILL.** The house claims you.")
                    self.combat_sessions.pop(ctx.guild.id, None)
                    self.reaction_used.pop(ctx.guild.id, None)
                    return

                # Check player conditions before their turn
                if player_char:
                    from data.static_data import POISONS
                    conds = [x.strip().lower() for x in (player_char.get("conditions_active") or "").split(",") if x.strip()]
                    # Stunned/paralyzed/incapacitated — skip turn
                    skip_conds = {"stunned", "paralyzed", "incapacitated"}
                    if any(c in skip_conds for c in conds):
                        matched = next(c for c in conds if c in skip_conds)
                        await ctx.send(f"⚔️ **{current}**'s turn — 💫 **{matched.upper()}**. Turn skipped.")
                        # Remove the skip condition after it takes effect
                        new_conds = [c for c in conds if c not in skip_conds]
                        set_char_field(player_char["discord_id"], "conditions_active", ", ".join(new_conds) if new_conds else None)
                        continue
                    # Poison DOT
                    for cond in conds:
                        if cond in POISONS and POISONS[cond]["dot"]:
                            p = POISONS[cond]
                            from data.static_data import roll_dice_str
                            _, dot_dmg = roll_dice_str(p["dot"])
                            new_hp = max(0, player_char["hp"] - dot_dmg)
                            set_char_field(player_char["discord_id"], "hp", new_hp)
                            player_char["hp"] = new_hp
                            await ctx.send(f"🧪 **{current}** takes **{dot_dmg} {p['dot_type']} damage** from {cond.title()}. HP: {new_hp}/{player_char.get('max_hp', new_hp)}")
                            if new_hp == 0:
                                await ctx.send(f"💀 **{current}** is DOWN from poison!")

                # Decrement condition durations and auto-remove expired ones
                if player_char:
                    gid = ctx.guild.id
                    pid = player_char["discord_id"]
                    player_durs = self.condition_durations.get(gid, {}).get(pid, {})
                    if player_durs:
                        expired = []
                        for cond_name in list(player_durs.keys()):
                            player_durs[cond_name] -= 1
                            if player_durs[cond_name] <= 0:
                                expired.append(cond_name)
                                del player_durs[cond_name]
                        if expired:
                            conds = [x.strip() for x in (player_char.get("conditions_active") or "").split(",") if x.strip()]
                            conds = [c for c in conds if c.lower() not in [e.lower() for e in expired]]
                            set_char_field(pid, "conditions_active", ", ".join(conds) if conds else None)
                            player_char["conditions_active"] = ", ".join(conds) if conds else None
                            await ctx.send(f"✨ **{current}** — {', '.join(e.title() for e in expired)} has worn off!")

                # Announce player turn and start timer
                # Clear dodging from previous turn
                if player_char:
                    conds = [x.strip() for x in (player_char.get("conditions_active") or "").split(",") if x.strip()]
                    if "dodging" in conds:
                        conds.remove("dodging")
                        set_char_field(player_char["discord_id"], "conditions_active", ", ".join(conds) if conds else None)
                turn_msg = f"⚔️ It is now **{current}**'s turn! ({COMBAT_TURN_TIMER}s to act)"
                if player_char:
                    active_conds = [x.strip() for x in (player_char.get("conditions_active") or "").split(",") if x.strip() and not x.strip().startswith("buff:")]
                    if active_conds:
                        turn_msg += f"\n⚠️ Active: **{', '.join(c.title() for c in active_conds)}**"
                await ctx.send(turn_msg)
                self.waiting_for_player = player_char["discord_id"] if player_char else None
                self.turn_task = asyncio.create_task(self._start_turn_timer(ctx, current))
                break

    async def _auto_end_combat(self, ctx):
        """Auto-end combat when all enemies are dead."""
        self._cancel_timer()
        self.combat_sessions.pop(ctx.guild.id, None)
        self.reaction_used.pop(ctx.guild.id, None)
        # Clear dodging from all players
        for ch in load_active_characters():
            conds = [x.strip() for x in (ch.get("conditions_active") or "").split(",") if x.strip()]
            if "dodging" in conds:
                conds.remove("dodging")
                set_char_field(ch["discord_id"], "conditions_active", ", ".join(conds) if conds else None)
        await ctx.send("🏳️ **All enemies defeated!** Combat ended.")
        await ctx.send(random.choice(STEWARD_COMBAT_END))

        # Loot and XP
        alive = [c for c in load_active_characters() if c["hp"] > 0]
        if alive:
            await self._roll_common_loot(ctx.channel)
            # Award pooled XP
            total_xp = self.combat_xp_pool.pop(ctx.guild.id, 0)
            if total_xp > 0:
                await self._award_xp(ctx.channel, total_xp)
            # Auto-level
            if XP_MODE == "auto":
                chars = load_active_characters()
                for c in chars:
                    from data.static_data import next_level_xp
                    nxt = next_level_xp(c["level"])
                    if nxt and (c.get("xp") or 0) >= nxt and c["level"] < 20:
                        await self._auto_level(ctx, c)

    async def _boss_loot_rolls(self, ctx, loot):
        """Need/Greed loot roll system for boss drops."""
        players = load_active_characters()
        if not players:
            return

        # Determine how many items drop based on party size
        # Formula: ceil(party_size * 0.4) — slightly less than half
        import math
        party_size = len(players)
        max_drops = max(1, math.ceil(party_size * 0.4))

        # Separate gold/consumables (auto-distribute) from gear (roll for)
        rollable = []
        auto_items = []
        for item in loot:
            item_lower = item.lower()
            if "gold" in item_lower or "potion" in item_lower or "vial" in item_lower or "tincture" in item_lower or "essence" in item_lower or "heart" in item_lower:
                auto_items.append(item)
            else:
                rollable.append(item)

        # Randomly select which gear pieces actually drop
        if len(rollable) > max_drops:
            rollable = random.sample(rollable, max_drops)

        # Show loot drop embed
        embed = discord.Embed(title="💎 Boss Loot Dropped!", color=discord.Color.gold())
        if rollable:
            embed.add_field(name="⚔️ Rolling For", value="\n".join(f"• {item}" for item in rollable), inline=False)
        if auto_items:
            embed.add_field(name="🎒 Auto-Distributed", value="\n".join(f"• {item}" for item in auto_items), inline=False)
        embed.set_footer(text=f"⏳ Rolling in 10 seconds... NEED > GREED ({max_drops}/{len(loot)-len(auto_items)} gear dropped)")
        await ctx.send(embed=embed)

        await asyncio.sleep(10)

        # Roll for each item
        results = []
        for item in rollable:
            item_lower = item.lower()
            # Determine who can NEED (use the item)
            is_weapon = item_lower in CAMPAIGN_WEAPONS or item_lower in WEAPONS
            is_armor = item_lower in CAMPAIGN_ARMOR

            need_players = []
            greed_players = []

            for c in players:
                can_need = False
                if is_weapon:
                    profs = get_weapon_proficiencies(c["class"], c["race"], c.get("notes", ""))
                    if item_lower in profs:
                        can_need = True
                elif is_armor:
                    base_armor = CAMPAIGN_ARMOR.get(item_lower, item_lower)
                    class_armor = CLASS_ARMOR_PROF.get(c["class"], set())
                    if base_armor in LIGHT_ARMOR and "light" in class_armor:
                        can_need = True
                    elif base_armor in MEDIUM_ARMOR and "medium" in class_armor:
                        can_need = True
                    elif base_armor in HEAVY_ARMOR and "heavy" in class_armor:
                        can_need = True
                    elif base_armor == "padded" and "light" in class_armor:
                        can_need = True
                else:
                    can_need = True  # Unknown item type — everyone can need

                if can_need:
                    need_players.append(c)
                else:
                    greed_players.append(c)

            # Roll: Need rolls (d100) beat Greed rolls (d100) always
            rolls = []
            for c in need_players:
                r = random.randint(1, 100)
                rolls.append((r + 1000, c, "NEED"))  # +1000 so need always > greed
            for c in greed_players:
                r = random.randint(1, 100)
                rolls.append((r, c, "GREED"))

            if not rolls:
                results.append(f"• **{item}** — No one can use it. DM distributes.")
                continue

            rolls.sort(key=lambda x: x[0], reverse=True)
            winner = rolls[0]
            roll_val = winner[0] - 1000 if winner[2] == "NEED" else winner[0]

            # Get rarity color
            rarity_info = WEAPON_RARITY.get(item_lower) or ARMOR_RARITY.get(item_lower)
            rarity_tag = f" ({rarity_info[0]})" if rarity_info else ""

            # Show all rolls
            all_rolls = ", ".join(
                f"{'**' if r is winner else ''}{r[1]['char_name']} {r[2]} {r[0]-1000 if r[2]=='NEED' else r[0]}{'**' if r is winner else ''}"
                for r in rolls
            )
            results.append(f"• **{item}**{rarity_tag} → **{winner[1]['char_name']}** 🏆\n  {all_rolls}")

            # Give item to winner — read fresh from DB each time
            fresh = get_db_char(winner[1]["discord_id"])
            inv = fresh.get("inventory") or "" if fresh else ""
            new_inv = f"{inv}, {item}".strip(", ")
            set_char_field(winner[1]["discord_id"], "inventory", new_inv)

        # Post results
        result_embed = discord.Embed(title="🎲 Loot Rolls — Results", color=discord.Color.green())
        result_embed.description = "\n".join(results)
        if auto_items:
            # Give gold/consumables to random players — read fresh each time
            for item in auto_items:
                recipient = random.choice(players)
                fresh = get_db_char(recipient["discord_id"])
                inv = fresh.get("inventory") or "" if fresh else ""
                set_char_field(recipient["discord_id"], "inventory", f"{inv}, {item}".strip(", "))
            result_embed.add_field(name="🎒 Distributed", value="\n".join(f"• {item}" for item in auto_items), inline=False)
        await ctx.send(embed=result_embed)
        # Show legendary weapon gif if one dropped
        import os
        LEGENDARY_LOOT_GIF = {
            "sigrids resolve": "vfx/entity_vfx/sigrids_resolve.gif",
            "aldric's paradox": "vfx/entity_vfx/aldrics_paradox.gif",
        }
        for item in rollable:
            gif = LEGENDARY_LOOT_GIF.get(item.lower())
            if gif and os.path.exists(gif):
                await ctx.send(f"✨ **LEGENDARY: {item.title()}**", file=discord.File(gif, filename=os.path.basename(gif)))
                break

    async def _auto_level(self, ctx, c):
        """Auto-level a character."""
        new_level = c["level"] + 1
        hit_die = CLASS_HP.get(c["class"], 8)
        hp_gain = (hit_die // 2 + 1) + modifier(c["constitution"])
        new_max_hp = (c.get("max_hp") or c["hp"]) + hp_gain
        new_hp = c["hp"] + hp_gain
        from data.db import get_db, set_slots
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE characters SET level=%s, max_hp=%s, hp=%s, hit_dice_remaining=hit_dice_remaining+1 WHERE discord_id=%s",
                    (new_level, new_max_hp, new_hp, c["discord_id"]))
        conn.commit(); cur.close(); conn.close()
        set_slots(c["discord_id"], get_slots_for_level(c["class"], new_level))
        embed = discord.Embed(title=f"🎉 LEVEL UP! {c['char_name']} is now Level {new_level}!", color=discord.Color.gold())
        embed.add_field(name="HP", value=f"{new_hp}/{new_max_hp} (+{hp_gain})", inline=True)
        features = CLASS_FEATURES.get(c["class"], {}).get(new_level, [])
        if features:
            embed.add_field(name="New Features", value="\n".join(f"• {f}" for f in features), inline=False)
        import os
        gif_path = "vfx/character_vfx/level_up.gif"
        if os.path.exists(gif_path):
            embed.set_image(url="attachment://level_up.gif")
            await ctx.send(embed=embed, file=discord.File(gif_path, filename="level_up.gif"))
        else:
            await ctx.send(embed=embed)

    # ── Enemy Attack Logic ─────────────────────────────────────────────────────

    async def _auto_enemy_attack(self, ctx, enemy_name, enemy):
        """Auto-resolve an enemy's turn."""
        chars = load_active_characters()
        alive = [c for c in chars if c["hp"] > 0]
        if not alive:
            return

        target = random.choice(alive)
        stats = ENEMY_ATTACK_STATS.get(enemy_name, (3, "1d6", 1, "damage"))
        atk_bonus, dmg_dice, dmg_bonus, dmg_type = stats

        atk_roll = random.randint(1, 20)
        is_crit = atk_roll == 20
        is_miss = atk_roll == 1
        total_atk = atk_roll + atk_bonus
        target_ac = target.get("ac", 10)
        hit = is_crit or (not is_miss and total_atk >= target_ac)

        msg = f"👹 **{enemy_name}** attacks **{target['char_name']}**!\n"
        msg += f"🎲 Attack: `{atk_roll}` +{atk_bonus} = **{total_atk}** vs AC {target_ac}"

        if is_crit:
            msg += " — 💥 **CRITICAL HIT!**"
        elif is_miss:
            msg += " — 💀 **NAT 1 — MISS!**"
        elif hit:
            msg += " — ✅ **HIT!**"
        else:
            msg += " — ❌ **MISS**"

        if hit:
            count, sides = dmg_dice.split("d")
            rolls = [random.randint(1, int(sides)) for _ in range(int(count))]
            if is_crit:
                rolls += [random.randint(1, int(sides)) for _ in range(int(count))]
            dmg = sum(rolls) + dmg_bonus

            temp = target.get("temp_hp", 0) or 0
            remaining_dmg = dmg
            # Raging: resistance to physical damage (halve)
            t_conds = [x.strip().lower() for x in (target.get("conditions_active") or "").split(",") if x.strip()]
            if "buff:raging" in t_conds:
                remaining_dmg = remaining_dmg // 2
            # Armor passive: damage resistance
            from data.static_data import ARMOR_PASSIVE
            t_armor = target.get("equipped_armor") or ""
            t_armor_passive = ARMOR_PASSIVE.get(t_armor, {})
            if t_armor_passive.get("resistance") and dmg_type.lower() in [r.lower() for r in t_armor_passive["resistance"]]:
                remaining_dmg = remaining_dmg // 2
            if temp > 0:
                absorbed = min(temp, remaining_dmg)
                remaining_dmg -= absorbed
                set_char_field(target["discord_id"], "temp_hp", temp - absorbed)

            new_hp = max(0, target["hp"] - remaining_dmg)
            set_char_field(target["discord_id"], "hp", new_hp)
            max_hp = target.get("max_hp") or target["hp"]

            msg += f"\n💥 Damage: `[{', '.join(str(r) for r in rolls)}]` +{dmg_bonus} = **{dmg} {dmg_type}**"
            msg += f"\n❤️ {target['char_name']} HP: **{new_hp}/{max_hp}**"
            if new_hp == 0:
                # Half-Orc Relentless Endurance
                if target.get("race") == "Half-Orc" and target.get("racial_uses", 0) < 1:
                    new_hp = 1
                    set_char_field(target["discord_id"], "hp", 1)
                    set_char_field(target["discord_id"], "racial_uses", 1)
                    msg += "\n🔥 **Relentless Endurance!** Drops to 1 HP instead of 0!"
                else:
                    msg += " 💀 **DOWN!**"

            if target.get("concentration"):
                dc = max(10, dmg // 2)
                conc_roll = random.randint(1, 20) + modifier(target["constitution"])
                if conc_roll < dc:
                    set_char_field(target["discord_id"], "concentration", None)
                    msg += f"\n⚠️ Concentration on **{target['concentration']}** broken!"

            # Apply enemy condition to player on hit
            # Strip suffixes: "Shadow A" → "Shadow", "The Echo (2)" → "The Echo"
            import re as _re
            base_enemy_name = _re.sub(r'\s+[A-Z]{1,2}$|\s*\(\d+\)$', '', enemy_name)
            enemy_cond = ENEMY_ON_HIT_CONDITION.get(enemy_name) or ENEMY_ON_HIT_CONDITION.get(base_enemy_name)
            if enemy_cond and random.random() <= enemy_cond["chance"]:
                cond_name = enemy_cond["condition"]
                # Check player resistance
                resistances = get_player_condition_resistance(target["class"], target["race"], target["level"])
                if resistances.get(cond_name) == "immune":
                    msg += f"\n🛡️ {target['char_name']} is **IMMUNE** to {cond_name}!"
                else:
                    # Make save
                    save_stat = enemy_cond["save_stat"]
                    save_dc = enemy_cond["save_dc"]
                    roll = random.randint(1, 20)
                    stat_mod = modifier(target[save_stat])
                    from data.static_data import CLASS_SAVE_PROFS as _CSP
                    save_prof = prof_bonus(target["level"]) if save_stat in _CSP.get(target["class"], set()) else 0
                    total_save = roll + stat_mod + save_prof
                    # Advantage if resistant
                    if resistances.get(cond_name) == "advantage":
                        roll2 = random.randint(1, 20)
                        total_save2 = roll2 + stat_mod + save_prof
                        total_save = max(total_save, total_save2)
                    if total_save < save_dc:
                        # Failed save — apply condition
                        existing = [x.strip() for x in (target.get("conditions_active") or "").split(",") if x.strip()]
                        if cond_name not in existing:
                            existing.append(cond_name)
                            set_char_field(target["discord_id"], "conditions_active", ", ".join(existing))
                        msg += f"\n😨 {target['char_name']} is **{cond_name.upper()}!** (save: {total_save} vs DC {save_dc})"
                    else:
                        msg += f"\n✅ {target['char_name']} resists {cond_name}! (save: {total_save} vs DC {save_dc})"

        await ctx.send(msg)

    async def _auto_enemy_attack_silent(self, ctx, enemy_name, enemy):
        """Same as _auto_enemy_attack but returns the message string instead of sending."""
        chars = load_active_characters()
        alive = [c for c in chars if c["hp"] > 0]
        if not alive:
            return f"👹 **{enemy_name}** — no targets."

        target = random.choice(alive)
        stats = ENEMY_ATTACK_STATS.get(enemy_name, (3, "1d6", 1, "damage"))
        atk_bonus, dmg_dice, dmg_bonus, dmg_type = stats
        atk_roll = random.randint(1, 20)
        is_crit = atk_roll == 20
        is_miss = atk_roll == 1
        total_atk = atk_roll + atk_bonus
        target_ac = target.get("ac", 10)
        hit = is_crit or (not is_miss and total_atk >= target_ac)

        line = f"👹 **{enemy_name}** → **{target['char_name']}**: `{atk_roll}`+{atk_bonus}={total_atk}"
        # Get flavor text for this enemy
        flavor_pool = ENEMY_ATTACK_FLAVOR.get(enemy_name, DEFAULT_ATTACK_FLAVOR)
        if is_crit:
            line += " 💥 **CRIT!**"
            flavor = random.choice(flavor_pool.get("crit", DEFAULT_ATTACK_FLAVOR["crit"]))
        elif is_miss or not hit:
            line += " ❌ MISS"
            flavor = random.choice(flavor_pool.get("miss", DEFAULT_ATTACK_FLAVOR["miss"]))
        else:
            line += " ✅ HIT"
            flavor = random.choice(flavor_pool.get("hit", DEFAULT_ATTACK_FLAVOR["hit"]))
        line += f"\n   *{flavor}*"

        if hit:
            count, sides = dmg_dice.split("d")
            rolls = [random.randint(1, int(sides)) for _ in range(int(count))]
            if is_crit:
                rolls += [random.randint(1, int(sides)) for _ in range(int(count))]
            dmg = sum(rolls) + dmg_bonus
            temp = target.get("temp_hp", 0) or 0
            remaining_dmg = dmg
            if temp > 0:
                absorbed = min(temp, remaining_dmg); remaining_dmg -= absorbed
                set_char_field(target["discord_id"], "temp_hp", temp - absorbed)
            new_hp = max(0, target["hp"] - remaining_dmg)
            set_char_field(target["discord_id"], "hp", new_hp)
            max_hp = target.get("max_hp") or target["hp"]
            line += f"\n   {dmg} {dmg_type} → HP: **{new_hp}/{max_hp}**"
            if new_hp == 0: line += " 💀 **DOWN!**"
            if target.get("concentration"):
                dc = max(10, dmg // 2)
                conc_roll = random.randint(1, 20) + modifier(target["constitution"])
                if conc_roll < dc:
                    set_char_field(target["discord_id"], "concentration", None)
                    line += f"\n   ⚠️ Concentration broken!"

            # Apply enemy condition to player on hit
            import re as _re
            base_enemy_name = _re.sub(r'\s+[A-Z]{1,2}$|\s*\(\d+\)$', '', enemy_name)
            enemy_cond_data = ENEMY_ON_HIT_CONDITION.get(enemy_name) or ENEMY_ON_HIT_CONDITION.get(base_enemy_name)
            if enemy_cond_data:
                # Normalize to list
                cond_list = enemy_cond_data if isinstance(enemy_cond_data, list) else [enemy_cond_data]
                for enemy_cond in cond_list:
                    if random.random() <= enemy_cond["chance"]:
                        cond_name = enemy_cond["condition"]
                        resistances = get_player_condition_resistance(target["class"], target["race"], target["level"])
                        if resistances.get(cond_name) == "immune":
                            line += f"\n   🛡️ {target['char_name']} is **IMMUNE** to {cond_name}!"
                        else:
                            save_stat = enemy_cond["save_stat"]
                            save_dc = enemy_cond["save_dc"]
                            roll = random.randint(1, 20)
                            stat_mod = modifier(target[save_stat])
                            from data.static_data import CLASS_SAVE_PROFS as _CSP
                            save_prof = prof_bonus(target["level"]) if save_stat in _CSP.get(target["class"], set()) else 0
                            total_save = roll + stat_mod + save_prof
                            if resistances.get(cond_name) == "advantage":
                                roll2 = random.randint(1, 20)
                                total_save = max(total_save, roll2 + stat_mod + save_prof)
                            if total_save < save_dc:
                                existing = [x.strip() for x in (target.get("conditions_active") or "").split(",") if x.strip()]
                                if cond_name not in existing:
                                    existing.append(cond_name)
                                    set_char_field(target["discord_id"], "conditions_active", ", ".join(existing))
                                    # Track duration
                                    dur = enemy_cond.get("duration", 3)
                                    if dur > 0:
                                        gid = ctx.guild.id
                                        self.condition_durations.setdefault(gid, {}).setdefault(target["discord_id"], {})[cond_name] = dur
                                line += f"\n   😨 {target['char_name']} is **{cond_name.upper()}!** (save: {total_save} vs DC {save_dc})"
                            else:
                                line += f"\n   ✅ {target['char_name']} resists {cond_name}! (save: {total_save} vs DC {save_dc})"
        return line

    async def _send_enemy_phase_embed(self, ctx, log_lines):
        """Send all enemy attacks as a single red-bordered embed."""
        embed = discord.Embed(title="⚔️ Enemy Phase", color=discord.Color.dark_red())
        embed.description = "\n\n".join(log_lines)
        await ctx.send(embed=embed)
        # Send death gif if someone went down
        if any("💀 **DOWN!**" in line for line in log_lines):
            import os
            death_gif = "vfx/character_vfx/died.gif"
            if os.path.exists(death_gif):
                await ctx.send(file=discord.File(death_gif, filename="died.gif"))

    # ── Loot ───────────────────────────────────────────────────────────────────

    async def _roll_common_loot(self, channel):
        chars = load_active_characters()
        if not chars:
            return
        recipients = [c for c in chars if c["hp"] > 0]
        if not recipients:
            return
        lines = []
        for c in recipients:
            roll = random.randint(1, 20)
            item = None
            for low, high, loot_item in COMMON_LOOT_TABLE:
                if low <= roll <= high:
                    item = loot_item
                    break
            if not item:
                continue
            items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
            items.append(item)
            set_char_field(c["discord_id"], "inventory", ", ".join(items))
            if item == "5 gold":
                set_char_field(c["discord_id"], "gold", (c.get("gold") or 0) + 5)
            elif item == "10 gold":
                set_char_field(c["discord_id"], "gold", (c.get("gold") or 0) + 10)
            lines.append(f"• **{c['char_name']}** received: {item}")
        if lines:
            embed = discord.Embed(title="💎 Loot Distributed!", color=discord.Color.gold())
            embed.description = "\n".join(lines)
            await channel.send(embed=embed)

    async def _award_xp(self, channel, xp_amount):
        if XP_MODE != "auto" or xp_amount <= 0:
            return
        chars = load_active_characters()
        if not chars:
            return
        player_count = self.get_active_player_count()
        per_player = xp_amount // player_count
        if per_player <= 0:
            return
        from data.db import get_db
        conn = get_db()
        cur = conn.cursor()
        for c in chars:
            new_xp = (c.get("xp") or 0) + per_player
            cur.execute("UPDATE characters SET xp = %s WHERE discord_id = %s", (new_xp, c["discord_id"]))
        conn.commit(); cur.close(); conn.close()
        await channel.send(f"⭐ **{xp_amount} XP** split across {player_count} players (**{per_player} each**)")

    # ── Commands ───────────────────────────────────────────────────────────────

    @commands.command(aliases=["battle","fight","f"])
    async def startcombat(self, ctx):
        self.combat_sessions[ctx.guild.id] = {"order": [], "turn": -1}
        chars = load_active_characters()
        rolls = []
        for c in chars:
            if c["hp"] <= 0:
                continue
            r = random.randint(1, 20)
            dex_mod = modifier(c["dexterity"])
            total = r + dex_mod
            self.combat_sessions[ctx.guild.id]["order"].append((c["char_name"], total))
            rolls.append(f"🎲 **{c['char_name']}**: `{r}` {mod_str(c['dexterity'])} = **{total}**")
        msg = "⚔️ **Combat started!** Initiative rolled:\n" + "\n".join(rolls) if rolls else "⚔️ **Combat started!**"
        msg += "\n\nDM: `/summon <enemy>` then `/startround` when ready."
        await ctx.send(msg)
        await ctx.send(random.choice(STEWARD_COMBAT_START))

    @commands.command(aliases=["go","begin","g"])
    async def startround(self, ctx):
        session = self.combat_sessions.get(ctx.guild.id)
        if not session or not session["order"]:
            await ctx.send("No initiative rolls yet."); return
        session["order"] = sorted(session["order"], key=lambda x: x[1], reverse=True)
        session["turn"] = -1  # Will be advanced to 0 by _advance_turn
        embed = discord.Embed(title="⚔️ Initiative Order", color=discord.Color.red())
        embed.description = "\n".join(f"**{i+1}.** {name} — {roll}" for i, (name, roll) in enumerate(session["order"]))
        await ctx.send(embed=embed)
        # Auto-advance to first turn
        await self._advance_turn(ctx)

    @commands.command(aliases=["next","n"])
    async def nextturn(self, ctx):
        session = self.combat_sessions.get(ctx.guild.id)
        if not session or not session["order"]:
            await ctx.send("No active combat."); return
        self._cancel_timer()
        await self._advance_turn(ctx)

    @commands.command(aliases=["end","peace","q"])
    async def endcombat(self, ctx):
        self._cancel_timer()
        self.combat_sessions.pop(ctx.guild.id, None)
        self.reaction_used.pop(ctx.guild.id, None)
        await ctx.send("🏳️ Combat ended.")
        alive = [c for c in load_active_characters() if c["hp"] > 0]
        if not alive:
            await ctx.send("💀 No survivors. No loot. No XP."); return
        enemies = self._get_enemies(ctx.guild.id)
        if enemies:
            await ctx.send(f"⚠️ Combat ended early. {len(enemies)} enemy(s) still alive — no loot or XP.")
            self.enemy_roster.pop(ctx.guild.id, None); return
        await self._roll_common_loot(ctx.channel)

    @commands.command()
    async def target(self, ctx, *, args: str = ""):
        """Player attacks an enemy. Auto-advances turn after."""
        # Turn check — only act on your turn (DMs exempt)
        from data.helpers import is_dm
        if self.waiting_for_player and self.waiting_for_player != ctx.author.id and not is_dm(ctx):
            await ctx.send("❌ It's not your turn.", delete_after=5); return
        # Rest lockout check
        conds = self.bot.get_cog("Conditions")
        if conds:
            unlock = conds._rest_lockout.get(ctx.author.id, 0)
            remaining = int(unlock - discord.utils.utcnow().timestamp())
            if remaining > 0:
                await ctx.send(f"⏳ You're still resting! Ready in **{remaining}s**."); return
        # Parse: last word might be a bonus number
        bonus = 0
        name = ""
        if args:
            parts = args.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].lstrip("-").isdigit():
                name, bonus = parts[0], int(parts[1])
            else:
                name, bonus = args, 0
        enemies = self._get_enemies(ctx.guild.id)
        # Auto-pick random enemy if no name specified
        if not name and enemies:
            name = random.choice(list(enemies.keys()))
        elif not enemies:
            await ctx.send("❌ No enemies in combat."); return
        match = next((k for k in enemies if k.lower() == name.lower()), None)
        if not match:
            # Try partial match — but prefer shortest match (most specific)
            partials = [k for k in enemies if name.lower() in k.lower()]
            match = min(partials, key=len) if partials else None
        if not match:
            await ctx.send(f"❌ No enemy named `{name}`."); return

        e = enemies[match]
        c = get_db_char(ctx.author.id)
        r = random.randint(1, 20)
        lucky_msg = ""
        debuff_msg = ""
        if c and r == 1 and c.get("race") == "Halfling":
            r = random.randint(1, 20)
            lucky_msg = " 🍀 Lucky reroll!"
        # Disadvantage from conditions (poisoned, frightened, blinded, restrained)
        if c:
            conds = [x.strip().lower() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
            disadvantage_conds = {"poisoned", "frightened", "blinded", "restrained", "prone"}
            has_disadvantage = any(cond in disadvantage_conds for cond in conds)
            has_advantage = "buff:inspired" in conds
            if has_advantage and has_disadvantage:
                pass  # cancel out
            elif has_disadvantage:
                r2 = random.randint(1, 20)
                if r2 < r: r = r2
                debuff_msg = " ⚠️ (disadvantage)"
            elif has_advantage:
                r2 = random.randint(1, 20)
                if r2 > r: r = r2
                debuff_msg = " ⬆️ (advantage)"
                # Consume inspired
                conds.remove("buff:inspired")
                set_char_field(c["discord_id"], "conditions_active", ", ".join(conds) if conds else None)
        is_crit, is_miss = r == 20, r == 1
        atk_bonus = bonus
        weapon_name = c["equipped_weapon"] if c and c.get("equipped_weapon") else None
        w_key = (weapon_name.lower() if weapon_name else "unarmed") if c else None
        # Resolve weapon data: check WEAPONS directly, then fall back to base weapon via CAMPAIGN_WEAPONS
        weapon_data = WEAPONS.get(w_key) if w_key else None
        if not weapon_data and w_key:
            base = CAMPAIGN_WEAPONS.get(w_key)
            if base:
                weapon_data = WEAPONS.get(base)

        if c and weapon_data:
            props = weapon_data[1].lower()
            stat_mod = max(modifier(c["strength"]), modifier(c["dexterity"])) if "finesse" in props else modifier(c["strength"])
            # Monk: can use DEX for unarmed and monk weapons
            if c["class"] == "Monk" and (w_key == "unarmed" or "simple" in props):
                stat_mod = max(modifier(c["strength"]), modifier(c["dexterity"]))
            atk_bonus += stat_mod + prof_bonus(c["level"])

        # Apply buff bonuses to attack
        buff_bonus = 0
        if c:
            conds = [x.strip().lower() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
            if "buff:blessed" in conds:
                buff_bonus += random.randint(1, 4)
            if "buff:strength" in conds and weapon_data and "ranged" not in weapon_data[1].lower():
                buff_bonus += 2
        atk_bonus += buff_bonus

        total = r + atk_bonus
        hit_target = is_crit or (not is_miss and total >= e["ac"])
        char_name = c["char_name"] if c else ctx.author.display_name

        if is_crit: result = "💥 **CRITICAL HIT!**"
        elif is_miss: result = "💀 **NAT 1 — MISS!**"
        elif hit_target: result = f"✅ **HIT!** (AC {e['ac']})"
        else: result = f"❌ **MISS** (needed {e['ac']})"

        msg = f"⚔️ **{char_name}** attacks **{match}**: `{r}` +{atk_bonus} = **{total}** → {result}{lucky_msg}{debuff_msg}"
        if not hit_target:
            msg += f"\n❤️ {match} HP: **{e['hp']}/{e['max_hp']}**"

        if hit_target and weapon_data:
            damage_str = weapon_data[0].split(" ")[0]
            # Monk unarmed: use martial arts die instead of "1"
            if w_key == "unarmed" and c and c.get("class") == "Monk":
                from data.static_data import get_monk_die
                damage_str = get_monk_die(c["level"])
            try:
                # Handle flat damage numbers (e.g. unarmed "1")
                if "d" not in damage_str:
                    flat_dmg = int(damage_str)
                    rolls = [flat_dmg]
                    dmg = flat_dmg
                    if is_crit: dmg += flat_dmg; rolls.append(flat_dmg)
                else:
                    rolls, dmg = roll_dice_str(damage_str)
                    if is_crit:
                        r2, d2 = roll_dice_str(damage_str); rolls += r2; dmg += d2
                if c and c["class"] == "Rogue":
                    sa_dice = SNEAK_ATTACK_DICE.get(c["level"], 1)
                    sa_rolls = [random.randint(1, 6) for _ in range(sa_dice)]
                    if is_crit:
                        sa_rolls += [random.randint(1, 6) for _ in range(sa_dice)]
                    dmg += sum(sa_rolls)
                    msg += f"\n🗡️ Sneak Attack: +{sum(sa_rolls)}"
                # Buff damage bonuses
                if c:
                    p_conds = [x.strip().lower() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
                    if "buff:strength" in p_conds: dmg += 2
                    if "buff:raging" in p_conds: dmg += 2
                # Weapon bonus damage
                from data.static_data import WEAPON_BONUS_DAMAGE, WEAPON_BONUS_TYPE, WEAPON_ON_KILL
                if w_key and w_key in WEAPON_BONUS_DAMAGE:
                    bonus_str = WEAPON_BONUS_DAMAGE[w_key]
                    if bonus_str.isdigit():
                        bonus_dmg = int(bonus_str)
                    else:
                        _, bonus_dmg = roll_dice_str(bonus_str)
                    dmg += bonus_dmg
                    bonus_type = WEAPON_BONUS_TYPE.get(w_key, "")
                    if bonus_type:
                        msg += f"\n⚡ +{bonus_dmg} {bonus_type} ({w_key.title()})"
                e["hp"] = max(0, e["hp"] - dmg)
                msg += f"\n💥 Damage: `[{', '.join(str(x) for x in rolls)}]` = **{dmg}** → {match} HP: **{e['hp']}/{e['max_hp']}**"
                # Sync attack VFX
                # Apply weapon effects
                weapon_key = c.get("equipped_weapon") if c else None
                if weapon_key and e["hp"] > 0:
                    immunities = BOSS_CONDITION_IMMUNITIES.get(match, set())
                    # On-crit effects
                    if is_crit and weapon_key in WEAPON_ON_CRIT:
                        effect = WEAPON_ON_CRIT[weapon_key]
                        cond_name = effect["condition"]
                        if cond_name in immunities:
                            msg += f"\n🔨 {weapon_key.title()}: **{cond_name.upper()}!** ...{match} is **IMMUNE**."
                        else:
                            if "active_conditions" not in e:
                                e["active_conditions"] = []
                            e["active_conditions"].append({"name": cond_name, "expires_in": effect["duration"]})
                            msg += f"\n🔨 {weapon_key.title()}: **{match}** is **{cond_name.upper()}!** ({effect['duration']} turn)"
                    # On-hit effects
                    if weapon_key in WEAPON_ON_HIT:
                        effect = WEAPON_ON_HIT[weapon_key]
                        if effect.get("effect") == "displace":
                            msg += f"\n⚡ {weapon_key.title()}: {match} must make WIS DC {effect['save_dc']} or be displaced 10 ft."
                if e["hp"] == 0:
                    msg += f"\n💀 **{match} is DEFEATED!**"
                    # Weapon on-kill effects
                    if w_key and w_key in WEAPON_ON_KILL:
                        kill_effect = WEAPON_ON_KILL[w_key]
                        if kill_effect["effect"] == "temp_hp":
                            set_char_field(ctx.author.id, "temp_hp", max(c.get("temp_hp", 0) or 0, kill_effect["value"]))
                            msg += f"\n🛡️ +{kill_effect['value']} temp HP ({w_key.title()})"
                        elif kill_effect["effect"] == "heal":
                            _, heal_amt = roll_dice_str(kill_effect["value"])
                            max_hp = c.get("max_hp") or c["hp"]
                            new_hp = min(max_hp, c["hp"] + heal_amt)
                            set_char_field(ctx.author.id, "hp", new_hp)
                            msg += f"\n❤️ +{heal_amt} HP ({w_key.title()})"
                    xp_val = e.get("xp", 0)
                    loot = e.get("loot", [])
                    session = self.combat_sessions.get(ctx.guild.id)
                    if session:
                        session["order"] = [(n, r) for n, r in session["order"] if n != f"👹 {match}"]
                    # Pool XP for end-of-combat award
                    self.combat_xp_pool[ctx.guild.id] = self.combat_xp_pool.get(ctx.guild.id, 0) + xp_val
                    del enemies[match]
                    await ctx.send(msg)
                    # Boss loot — Need/Greed roll system
                    if loot:
                        await self._boss_loot_rolls(ctx, loot)
                    # Check if all enemies dead
                    if not self._get_enemies(ctx.guild.id):
                        await self._auto_end_combat(ctx)
                    else:
                        # Auto-advance after player acted
                        self._cancel_timer()
                        await self._advance_turn(ctx)
                    return
            except Exception:
                pass

        # Send with weapon gif
        import os
        weapon_gif_path = get_weapon_gif(c.get("equipped_weapon") if c else None)
        gif = resolve_gif(weapon_gif_path, is_crit)
        if gif and os.path.exists(gif):
            await ctx.send(msg, file=discord.File(gif, filename=os.path.basename(gif)))
        else:
            await ctx.send(msg)
        # Auto-advance after player acted
        self._cancel_timer()
        await self._advance_turn(ctx)

    @commands.command()
    async def dodge(self, ctx):
        """Voluntarily take the Dodge action. Attacks against you have disadvantage until your next turn."""
        from data.helpers import is_dm
        if self.waiting_for_player != ctx.author.id and not is_dm(ctx):
            await ctx.send("❌ It's not your turn."); return
        c = get_db_char(self.waiting_for_player)
        char_name = c["char_name"] if c else ctx.author.display_name
        # Mark dodging
        conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()] if c else []
        if "dodging" not in conds:
            conds.append("dodging")
            set_char_field(self.waiting_for_player, "conditions_active", ", ".join(conds))
        await ctx.send(f"🛡️ **{char_name}** takes the **Dodge** action. Attacks against them have disadvantage until their next turn.")
        self._cancel_timer()
        await self._advance_turn(ctx)

    @commands.command()
    async def skip(self, ctx):
        """DM: Force skip the current player's turn."""
        from data.helpers import is_dm
        if not is_dm(ctx):
            await ctx.send("❌ Only the DM can skip turns."); return
        if not self.waiting_for_player:
            await ctx.send("❌ No one's turn to skip."); return
        c = get_db_char(self.waiting_for_player)
        char_name = c["char_name"] if c else "Unknown"
        await ctx.send(f"⏭️ **{char_name}**'s turn skipped by DM.")
        self._cancel_timer()
        await self._advance_turn(ctx)

    @commands.command()
    async def bestiary(self, ctx, tier: int = 0):
        """Show all creatures grouped by tier. Use !bestiary 2 to filter."""
        tiers = {1: [], 2: [], 3: [], 4: []}
        for key, data in HOSTILE_MENAGERIE.items():
            t = data.get("tier", 1)
            tiers.setdefault(t, []).append((key, data))
        tier_names = {1: "Fodder (Level 1+)", 2: "Mid-Threat (Level 2-3+)", 3: "Boss-Adjacent (Level 3-5+)", 4: "Nightmare (Level 5-8+)"}
        embed = discord.Embed(title="📖 Bestiary", color=discord.Color.dark_red())
        for t in [1, 2, 3, 4]:
            if tier and tier != t:
                continue
            creatures = sorted(tiers.get(t, []), key=lambda x: x[1].get("xp", 0))
            if not creatures:
                continue
            lines = [f"`!sp {k}` — {d['name']} (HP {d['hp']}, AC {d['ac']}, XP {d['xp']})" for k, d in creatures]
            embed.add_field(name=f"⚔️ Tier {t}: {tier_names[t]}", value="\n".join(lines), inline=False)
        embed.set_footer(text="Use !bestiary <tier> to filter. Use !sp <key> <count> to spawn.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["spawn","sp"])
    async def summon(self, ctx, *, args: str):
        """Spawn enemies. Usage: !sp shadow 3 or !sp test boss"""
        # Parse: last word might be a count
        parts = args.rsplit(None, 1)
        if len(parts) == 2 and parts[1].isdigit():
            key, count = parts[0], int(parts[1])
        else:
            key, count = args, 1
        if key.lower() not in HOSTILE_MENAGERIE:
            await ctx.send(f"❌ Unknown. Options: {', '.join(HOSTILE_MENAGERIE.keys())}"); return
        preset = HOSTILE_MENAGERIE[key.lower()]
        # Tier warning
        min_lvl = preset.get("min_level", 1)
        tier = preset.get("tier", 1)
        chars = load_active_characters()
        avg_level = sum(c.get("level", 1) for c in chars) / max(len(chars), 1) if chars else 1
        if avg_level < min_lvl:
            await ctx.send(f"⚠️ **{preset['name']}** is Tier {tier} (recommended level {min_lvl}+). Your party averages level {int(avg_level)}. Spawning anyway...")
        enemies = self._get_enemies(ctx.guild.id)
        session = self.combat_sessions.get(ctx.guild.id)
        player_count = self.get_active_player_count()
        if player_count > 5: hp_scale = 1.0 + 0.25 * (player_count - 5)
        elif player_count < 5: hp_scale = max(0.6, 1.0 - 0.15 * (5 - player_count))
        else: hp_scale = 1.0
        scaled_hp = max(1, int(preset["hp"] * hp_scale))
        spawned = []
        for i in range(count):
            label = chr(65 + i) if i < 26 else chr(65 + (i // 26) - 1) + chr(65 + (i % 26))
            name = preset["name"] if count == 1 else f"{preset['name']} {label}"
            base = name; j = 2
            while name in enemies: name = f"{base} ({j})"; j += 1
            entry = {"hp": scaled_hp, "max_hp": scaled_hp, "ac": preset["ac"],
                     "conditions": [], "legendary_actions": preset.get("la", 0),
                     "legendary_resistances": preset.get("lr", 0),
                     "max_la": preset.get("la", 0), "notes": preset.get("traits", ""),
                     "xp": preset.get("xp", 0), "loot": preset.get("loot", [])}
            enemies[name] = entry
            if session is not None:
                roll = random.randint(1, 20)
                session["order"].append((f"👹 {name}", roll))
            spawned.append(name)
        embed = discord.Embed(title=f"👹 Summoned: {preset['name']}" + (f" ×{count}" if count > 1 else ""), color=discord.Color.dark_red())
        embed.add_field(name="HP", value=f"{scaled_hp}" + (f" (scaled for {player_count} players)" if hp_scale != 1.0 else ""), inline=True)
        embed.add_field(name="AC", value=f"{preset['ac']}", inline=True)
        embed.add_field(name="Attacks", value=preset.get("attacks", "—"), inline=False)
        # Show on-hit afflictions
        on_hit = ENEMY_ON_HIT_CONDITION.get(preset["name"])
        if on_hit:
            if isinstance(on_hit, list):
                lines = [f"{int(e['chance']*100)}%: **{e['condition'].title()}** ({e['save_stat'].upper()} DC {e['save_dc']})" for e in on_hit]
                embed.add_field(name="⚠️ On Hit", value="\n".join(lines), inline=False)
            else:
                embed.add_field(name="⚠️ On Hit", value=f"{int(on_hit['chance']*100)}% chance: **{on_hit['condition'].title()}** ({on_hit['save_stat'].upper()} DC {on_hit['save_dc']}, {on_hit['duration']} turn{'s' if on_hit['duration']!=1 else ''})", inline=False)
        # Spawn gif if available
        import os
        spawn_gif = ENEMY_SPAWN_GIF.get(preset["name"]) or preset.get("spawn_gif")
        if spawn_gif and os.path.exists(spawn_gif):
            embed.set_image(url=f"attachment://{os.path.basename(spawn_gif)}")
            await ctx.send(embed=embed, file=discord.File(spawn_gif, filename=os.path.basename(spawn_gif)))
        else:
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Combat(bot))
