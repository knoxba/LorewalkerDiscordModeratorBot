import random
import os
import discord
from discord.ext import commands

from data.db import get_db_char, set_char_field, get_db, set_slots
from data.helpers import dm_reply
from data.static_data import (
    CLASS_HP, CLASS_FEATURES, ASI_LEVELS, FEATS, modifier, prof_bonus,
    get_slots_for_level, next_level_xp, get_class_title, CLASS_TITLES,
    MULTICLASS_SLOT_TABLE, CASTER_WEIGHT, CLASS_SLOT_TABLE,
)


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def xp(self, ctx):
        c = get_db_char(ctx.author.id)
        if not c: return
        nxt = next_level_xp(c["level"])
        await ctx.send(f"⭐ **{c['char_name']}** XP: **{c.get('xp',0)}** / {nxt or '—'}")

    @commands.command()
    async def levelup(self, ctx, mode: str = ""):
        c = get_db_char(ctx.author.id)
        if not c: return
        current_level = c["level"]
        if current_level >= 20: await ctx.send("Max level."); return
        nxt = next_level_xp(current_level)
        if nxt and c.get("xp", 0) < nxt: await ctx.send(f"❌ Need **{nxt}** XP, have **{c.get('xp',0)}**."); return

        # Determine how many levels to gain
        levels_to_gain = 1
        if mode.lower() == "all":
            lvl = current_level
            while lvl < 20:
                req = next_level_xp(lvl)
                if req and c.get("xp", 0) >= req:
                    lvl += 1
                else:
                    break
            levels_to_gain = lvl - current_level

        total_hp_gain = 0
        hit_die = CLASS_HP.get(c["class"], 8)
        for _ in range(levels_to_gain):
            total_hp_gain += (hit_die // 2 + 1) + modifier(c["constitution"])

        new_level = current_level + levels_to_gain
        new_max_hp = (c.get("max_hp") or c["hp"]) + total_hp_gain
        new_hp = c["hp"] + total_hp_gain
        new_slots = get_slots_for_level(c["class"], new_level)
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE characters SET level=%s, max_hp=%s, hp=%s, hit_dice_remaining=hit_dice_remaining+%s WHERE discord_id=%s",
                    (new_level, new_max_hp, new_hp, levels_to_gain, ctx.author.id))
        conn.commit(); cur.close(); conn.close()
        set_slots(ctx.author.id, new_slots)
        new_title = get_class_title(c["class"], new_level)
        old_title = get_class_title(c["class"], current_level)
        embed = discord.Embed(title=f"🎉 Level Up! {c['char_name']} is now level {new_level}!" + (f" (+{levels_to_gain})" if levels_to_gain > 1 else ""), color=discord.Color.gold())
        if new_title != old_title:
            embed.add_field(name="🏅 New Title", value=f"**{new_title}**", inline=False)
        embed.add_field(name="HP", value=f"{new_hp}/{new_max_hp} (+{total_hp_gain})", inline=True)
        embed.add_field(name="Prof Bonus", value=f"+{prof_bonus(new_level)}", inline=True)
        # Collect all features gained across levels
        all_features = []
        for lvl in range(current_level + 1, new_level + 1):
            features = CLASS_FEATURES.get(c["class"], {}).get(lvl, [])
            if features:
                all_features.extend(f"Lv{lvl}: {f}" for f in features)
        if all_features:
            embed.add_field(name="New Features", value="\n".join(f"• {f}" for f in all_features), inline=False)
        asi_gained = [lvl for lvl in range(current_level + 1, new_level + 1) if lvl in ASI_LEVELS]
        if asi_gained:
            embed.add_field(name="⬆️ ASI", value=f"{len(asi_gained)} ASI(s) available! Use `/asi <stat>` or `/takefeat <feat>`", inline=False)
        gif_path = "vfx/character_vfx/level_up.gif"
        if os.path.exists(gif_path):
            embed.set_image(url="attachment://level_up.gif")
            await ctx.send(embed=embed, file=discord.File(gif_path, filename="level_up.gif"))
        else:
            await ctx.send(embed=embed)

    @commands.command()
    async def asi(self, ctx, stat: str, amount: int = 2):
        stat_map = {"str":"strength","dex":"dexterity","con":"constitution","int":"intelligence","wis":"wisdom","cha":"charisma",
                    "strength":"strength","dexterity":"dexterity","constitution":"constitution","intelligence":"intelligence","wisdom":"wisdom","charisma":"charisma"}
        if stat.lower() not in stat_map: await ctx.send("❌ Use: str/dex/con/int/wis/cha"); return
        c = get_db_char(ctx.author.id)
        if not c: return
        if c["level"] not in ASI_LEVELS: await ctx.send(f"❌ ASIs at levels {sorted(ASI_LEVELS)}."); return
        if amount not in (1, 2): await ctx.send("❌ Amount must be 1 or 2."); return
        # Track ASI spending: store in notes as [ASI_SPENT_LVL_X:N]
        import re
        notes = c.get("notes") or ""
        spent_match = re.search(rf"\[ASI_SPENT_LVL_{c['level']}:(\d+)\]", notes)
        spent = int(spent_match.group(1)) if spent_match else 0
        if spent + amount > 2:
            await ctx.send(f"❌ Already spent **{spent}/2** ASI points at level {c['level']}. {2-spent} remaining."); return
        field = stat_map[stat.lower()]
        new_val = min(20, c[field] + amount)
        set_char_field(ctx.author.id, field, new_val)
        # Update spent tracker
        new_spent = spent + amount
        if spent_match:
            notes = re.sub(rf"\[ASI_SPENT_LVL_{c['level']}:\d+\]", f"[ASI_SPENT_LVL_{c['level']}:{new_spent}]", notes)
        else:
            notes = (notes + f"\n[ASI_SPENT_LVL_{c['level']}:{new_spent}]").strip()
        set_char_field(ctx.author.id, "notes", notes)
        remaining = 2 - new_spent
        await ctx.send(f"⬆️ **{field.title()}**: {c[field]} → **{new_val}** ({remaining} ASI point{'s' if remaining != 1 else ''} remaining)")

    @commands.command()
    async def feats(self, ctx):
        embed = discord.Embed(title="🏆 Available Feats", color=discord.Color.gold())
        embed.description = "\n".join(f"**{k.title()}** — {v[:80]}" for k, v in FEATS.items())
        await ctx.send(embed=embed)

    @commands.command()
    async def takefeat(self, ctx, *, feat_name: str):
        if feat_name.lower() not in FEATS: await ctx.send("❌ Unknown feat."); return
        c = get_db_char(ctx.author.id)
        if not c: return
        if c["level"] not in ASI_LEVELS: await ctx.send("❌ Feats at ASI levels only."); return
        existing = c.get("notes") or ""
        set_char_field(ctx.author.id, "notes", (existing + f"\n[Feat] {feat_name.title()}").strip())
        embed = discord.Embed(title=f"🏆 {c['char_name']} took **{feat_name.title()}**!", color=discord.Color.gold())
        embed.description = FEATS[feat_name.lower()]
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
