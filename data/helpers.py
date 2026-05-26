"""Shared helpers for all cogs."""

def is_dm(ctx):
    return any(r.name.lower() in ("dm","dungeon master","game master","gm") for r in ctx.author.roles)

async def dm_reply(ctx, content=None, embed=None, file=None):
    """Send to DMs for players, in-channel for DM."""
    if is_dm(ctx):
        kwargs = {}
        if content: kwargs["content"] = content
        if embed: kwargs["embed"] = embed
        if file: kwargs["file"] = file
        await ctx.send(**kwargs)
    else:
        try:
            kwargs = {}
            if content: kwargs["content"] = content
            if embed: kwargs["embed"] = embed
            if file: kwargs["file"] = file
            await ctx.author.send(**kwargs)
            await ctx.send(f"📬 Sent to your DMs.", delete_after=5)
        except Exception:
            # DMs closed — fall back to channel
            kwargs = {}
            if content: kwargs["content"] = content
            if embed: kwargs["embed"] = embed
            if file: kwargs["file"] = file
            await ctx.send(**kwargs)

async def check_auto_level(ctx, discord_id):
    """Check if a character has enough XP to level up, and auto-level them."""
    from data.db import get_db_char, set_char_field, get_db, set_slots
    from data.static_data import next_level_xp, CLASS_HP, modifier, prof_bonus, get_slots_for_level, CLASS_FEATURES, get_class_title, ASI_LEVELS
    import discord as _discord, os
    c = get_db_char(discord_id)
    if not c or c["level"] >= 20:
        return
    nxt = next_level_xp(c["level"])
    if not nxt or (c.get("xp") or 0) < nxt:
        return
    # Level up (all levels at once)
    current_level = c["level"]
    lvl = current_level
    while lvl < 20:
        req = next_level_xp(lvl)
        if req and (c.get("xp") or 0) >= req:
            lvl += 1
        else:
            break
    levels_gained = lvl - current_level
    if levels_gained <= 0:
        return
    hit_die = CLASS_HP.get(c["class"], 8)
    total_hp_gain = sum((hit_die // 2 + 1) + modifier(c["constitution"]) for _ in range(levels_gained))
    new_level = current_level + levels_gained
    new_max_hp = (c.get("max_hp") or c["hp"]) + total_hp_gain
    new_hp = c["hp"] + total_hp_gain
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE characters SET level=%s, max_hp=%s, hp=%s, hit_dice_remaining=hit_dice_remaining+%s WHERE discord_id=%s",
                (new_level, new_max_hp, new_hp, levels_gained, discord_id))
    conn.commit(); cur.close(); conn.close()
    set_slots(discord_id, get_slots_for_level(c["class"], new_level))
    new_title = get_class_title(c["class"], new_level)
    embed = _discord.Embed(title=f"🎉 LEVEL UP! {c['char_name']} is now Level {new_level}!" + (f" (+{levels_gained})" if levels_gained > 1 else ""), color=_discord.Color.gold())
    embed.add_field(name="HP", value=f"{new_hp}/{new_max_hp} (+{total_hp_gain})", inline=True)
    embed.add_field(name="Prof Bonus", value=f"+{prof_bonus(new_level)}", inline=True)
    all_features = []
    for l in range(current_level + 1, new_level + 1):
        features = CLASS_FEATURES.get(c["class"], {}).get(l, [])
        if features:
            all_features.extend(f"Lv{l}: {f}" for f in features)
    if all_features:
        embed.add_field(name="New Features", value="\n".join(f"• {f}" for f in all_features), inline=False)
    gif_path = "vfx/character_vfx/level_up.gif"
    if os.path.exists(gif_path):
        embed.set_image(url="attachment://level_up.gif")
        await ctx.send(embed=embed, file=_discord.File(gif_path, filename="level_up.gif"))
    else:
        await ctx.send(embed=embed)
