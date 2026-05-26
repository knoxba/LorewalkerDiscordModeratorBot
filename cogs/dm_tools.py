import random
import discord
from discord.ext import commands
from functools import wraps

from _config import DREAD_SECRET_THRESHOLD, XP_MODE, ACTIVE_PLAYERS
from data.db import get_db_char, set_char_field, load_all_characters, load_active_characters, get_db
from data.static_data import modifier, mod_str, prof_bonus, CLASS_SAVE_PROFS, SKILL_TO_STAT, CONDITION_EFFECTS


def is_dm(ctx):
    return any(r.name.lower() in ("dm","dungeon master","game master","gm") for r in ctx.author.roles)

def dm_only(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if not is_dm(ctx):
            await ctx.send("❌ Only the DM can use this command."); return
        return await func(self, ctx, *args, **kwargs)
    return wrapper


class DMTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def stealth_respond(self, ctx, embed=None, text=None):
        try:
            dm_channel = await ctx.author.create_dm()
            if embed: await dm_channel.send(embed=embed)
            elif text: await dm_channel.send(text)
        except Exception:
            if embed: await ctx.send(embed=embed, delete_after=10)
            elif text: await ctx.send(text, delete_after=10)

    # ── Whisper ────────────────────────────────────────────────────────────────

        except Exception as e:
            await ctx.send(f"❌ Sync error: {e}")

    @commands.command()
    @dm_only
    async def whisper(self, ctx, member: discord.Member, *, message: str):
        try:
            dm_channel = await member.create_dm()
            embed = discord.Embed(description=message, color=discord.Color.dark_purple())
            embed.set_author(name="🕯️ The Steward leans close and whispers...")
            embed.set_footer(text="Do they need to know? ...Would they believe you if you told them?")
            await dm_channel.send(embed=embed)
            await ctx.message.delete()
            await ctx.send(f"✅ Whispered to {member.display_name}.", delete_after=3)
        except Exception:
            await ctx.send(f"❌ Couldn't DM {member.display_name}.")

    # ── Fears & Dreams ─────────────────────────────────────────────────────────

    @commands.command()
    @dm_only
    async def fears(self, ctx, member: discord.Member):
        try: await ctx.message.delete()
        except: pass
        c = get_db_char(member.id)
        if not c: return
        embed = discord.Embed(title=f"😱 {c['char_name']}'s Fears", color=discord.Color.dark_red())
        embed.add_field(name="Character Fear", value=c.get("char_fear") or "Not set", inline=False)
        embed.add_field(name="Player Fear (real)", value=c.get("player_fear") or "Not set", inline=False)
        await self.stealth_respond(ctx, embed=embed)

    @commands.command()
    @dm_only
    async def dreams(self, ctx, member: discord.Member):
        try: await ctx.message.delete()
        except: pass
        c = get_db_char(member.id)
        if not c: return
        embed = discord.Embed(title=f"✨ {c['char_name']}'s Dream", color=discord.Color.gold())
        embed.add_field(name="Deepest Want", value=c.get("char_dream") or "Not set", inline=False)
        await self.stealth_respond(ctx, embed=embed)

    @commands.command()
    @dm_only
    async def allfears(self, ctx):
        try: await ctx.message.delete()
        except: pass
        chars = load_all_characters()
        if not chars: return
        embed = discord.Embed(title="😱 All Player Fears", color=discord.Color.dark_red())
        for c in chars:
            embed.add_field(name=c["char_name"], value=f"**Character:** {c.get('char_fear') or '—'}\n**Player:** {c.get('player_fear') or '—'}", inline=False)
        await self.stealth_respond(ctx, embed=embed)

    # ── Dread ──────────────────────────────────────────────────────────────────

    @commands.command()
    @dm_only
    async def dread(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        c = get_db_char(target.id)
        if not c: return
        level = c.get("dread", 0) or 0
        effects = {0:"Normal",1:"Disadv Investigation",2:"DM may lie about descriptions",3:"Disadv Wisdom saves",4:"DM may lie about one die result"}
        await self.stealth_respond(ctx, text=f"👁️ **{c['char_name']}** Dread: **{level}** — {effects.get(min(level,4),'Alternate reality')}")

    @commands.command()
    @dm_only
    async def disarm(self, ctx, member: discord.Member = None):
        """DM: Strip weapons from a player (or all players). They can't attack until rearmed."""
        if member:
            c = get_db_char(member.id)
            if not c: return
            set_char_field(member.id, "equipped_weapon", "unarmed")
            await ctx.send(f"🚫 **{c['char_name']}** has been disarmed. Attacks deal 1 + STR mod bludgeoning.")
        else:
            chars = load_active_characters()
            for c in chars:
                set_char_field(c["discord_id"], "equipped_weapon", "unarmed")
            await ctx.send(f"🚫 **All players** disarmed. Attacks deal 1 + STR mod bludgeoning.")

    @commands.command()
    @dm_only
    async def rearm(self, ctx, member: discord.Member = None):
        """DM: Allow players to equip weapons again (doesn't auto-equip — they must !equip)."""
        if member:
            c = get_db_char(member.id)
            if not c: return
            set_char_field(member.id, "equipped_weapon", None)
            await ctx.send(f"⚔️ **{c['char_name']}** can equip weapons again.")
        else:
            chars = load_active_characters()
            for c in chars:
                set_char_field(c["discord_id"], "equipped_weapon", None)
            await ctx.send(f"⚔️ **All players** can equip weapons again. Use `/equip <weapon>`.")

    @commands.command()
    @dm_only
    async def dmhp(self, ctx, member: discord.Member, amount: int):
        """DM: Modify a player's HP directly. Use negative for damage. Usage: !dmhp @player -5"""
        c = get_db_char(member.id)
        if not c: await ctx.send("❌ No character found."); return
        max_hp = c.get("max_hp") or c["hp"]
        new_hp = max(0, min(max_hp, c["hp"] + amount))
        set_char_field(member.id, "hp", new_hp)
        if amount < 0:
            await ctx.send(f"💔 **{c['char_name']}** takes **{abs(amount)} damage** → HP: **{new_hp}/{max_hp}**" + (" 💀 **DOWN!**" if new_hp == 0 else ""))
        else:
            await ctx.send(f"❤️ **{c['char_name']}** heals **{amount} HP** → HP: **{new_hp}/{max_hp}**")

    @commands.command()
    @dm_only
    async def dmhit(self, ctx, *, args: str):
        """DM: Deal flat damage to an enemy. Usage: !dmhit <enemy name> <damage>"""
        parts = args.rsplit(None, 1)
        if len(parts) < 2 or not parts[1].isdigit():
            await ctx.send("❌ Usage: `!dmhit <enemy name> <damage>`"); return
        name, dmg = parts[0], int(parts[1])
        combat = self.bot.get_cog("Combat")
        if not combat: await ctx.send("❌ No active combat."); return
        enemies = combat._get_enemies(ctx.guild.id)
        match = next((k for k in enemies if k.lower() == name.lower()), None)
        if not match:
            match = next((k for k in enemies if name.lower() in k.lower()), None)
        if not match:
            await ctx.send(f"❌ No enemy named `{name}`."); return
        e = enemies[match]
        e["hp"] = max(0, e["hp"] - dmg)
        msg = f"⚡ DM strikes **{match}** for **{dmg} damage** → HP: **{e['hp']}/{e['max_hp']}**"
        if e["hp"] == 0:
            msg += f"\n💀 **{match} is DEFEATED!**"
            session = combat.combat_sessions.get(ctx.guild.id)
            if session:
                session["order"] = [(n, r) for n, r in session["order"] if n != f"👹 {match}"]
            combat.combat_xp_pool[ctx.guild.id] = combat.combat_xp_pool.get(ctx.guild.id, 0) + e.get("xp", 0)
            del enemies[match]
        await ctx.send(msg)
        if not enemies:
            await combat._auto_end_combat(ctx)

    @commands.command()
    @dm_only
    async def stopregen(self, ctx, *, enemy_name: str):
        """DM: Disable regeneration on an enemy. Usage: !stopregen Depth Horror"""
        combat = self.bot.get_cog("Combat")
        if not combat: await ctx.send("❌ No active combat."); return
        enemies = combat._get_enemies(ctx.guild.id)
        match = next((k for k in enemies if enemy_name.lower() in k.lower()), None)
        if not match: await ctx.send(f"❌ No enemy named `{enemy_name}`."); return
        enemies[match]["regen"] = 0
        await ctx.send(f"🩸 **{match}** — regeneration DISABLED.")

    @commands.command()
    @dm_only
    async def classchallenge(self, ctx, member: discord.Member):
        """DM: Award a class challenge bonus. Grants inspiration + 50 XP."""
        c = get_db_char(member.id)
        if not c: await ctx.send("❌ No character found."); return
        set_char_field(member.id, "inspiration", 1)
        xp = (c.get("xp") or 0) + 50
        set_char_field(member.id, "xp", xp)
        await ctx.send(f"⚡ **{c['char_name']}** completes a **Class Challenge!**\n🌟 Gained **Inspiration** + **50 XP** (Total: {xp})")
        from data.helpers import check_auto_level
        await check_auto_level(ctx, member.id)

    @commands.command()
    @dm_only
    async def adddread(self, ctx, member: discord.Member, amount: int = 1):
        c = get_db_char(member.id)
        if not c: return
        try: await ctx.message.delete()
        except: pass
        new_val = (c.get("dread", 0) or 0) + amount
        set_char_field(member.id, "dread", new_val)
        await self.stealth_respond(ctx, text=f"👁️ **{c['char_name']}** Dread increased to **{new_val}**.")
        # Post flavor text in the channel (players see this but don't know why)
        from data.static_data import DREAD_INCREASE_FLAVOR
        import random
        flavors = DREAD_INCREASE_FLAVOR.get(min(new_val, 6), DREAD_INCREASE_FLAVOR[1])
        flavor = random.choice(flavors)
        for channel in ctx.guild.text_channels:
            if "house" in channel.name.lower() or "campaign" in channel.name.lower() or "the-house" in channel.name.lower():
                import os
                gif_path = "vfx/entity_vfx/dread.gif"
                if os.path.exists(gif_path):
                    await channel.send(flavor, file=discord.File(gif_path, filename="dread.gif"))
                else:
                    await channel.send(flavor)
                break

    @commands.command()
    @dm_only
    async def removedread(self, ctx, member: discord.Member, amount: int = 1):
        c = get_db_char(member.id)
        if not c: return
        try: await ctx.message.delete()
        except: pass
        new_val = max(0, (c.get("dread", 0) or 0) - amount)
        set_char_field(member.id, "dread", new_val)
        await self.stealth_respond(ctx, text=f"👁️ **{c['char_name']}** Dread reduced to **{new_val}**.")

    @commands.command()
    @dm_only
    async def dreadcheck(self, ctx):
        """DM: Show all players' Dread levels (stealth — only DM sees)."""
        chars = load_active_characters()
        if not chars: await ctx.send("❌ No characters."); return
        try: await ctx.message.delete()
        except: pass
        lines = sorted([(c.get("dread", 0) or 0, c["char_name"]) for c in chars], reverse=True)
        msg = "👁️ **Dread Levels:**\n" + "\n".join(f"  {name}: **{d}**" for d, name in lines)
        await self.stealth_respond(ctx, text=msg)

    @commands.command()
    @dm_only
    async def dreadall(self, ctx):
        try: await ctx.message.delete()
        except: pass
        chars = load_all_characters()
        if not chars: return
        embed = discord.Embed(title="👁️ Party Dread Levels", color=discord.Color.dark_purple())
        for c in chars:
            level = c.get("dread", 0) or 0
            bar = "█" * level + "░" * (6 - level)
            embed.add_field(name=c["char_name"], value=f"`[{bar}]` {level}", inline=False)
        await self.stealth_respond(ctx, embed=embed)

    # ── Roster ─────────────────────────────────────────────────────────────────

    @commands.command()
    @dm_only
    async def activate(self, ctx, *members: discord.Member):
        activated = []
        for member in members:
            c = get_db_char(member.id)
            if not c: continue
            set_char_field(member.id, "active", 1)
            activated.append(c["char_name"])
        if activated:
            await ctx.send(f"✅ Active roster updated. Added: {', '.join(activated)}")

    @commands.command()
    @dm_only
    async def deactivate(self, ctx, *members: discord.Member):
        deactivated = []
        for member in members:
            c = get_db_char(member.id)
            if not c: continue
            set_char_field(member.id, "active", 0)
            deactivated.append(c["char_name"])
        if deactivated:
            await ctx.send(f"✅ Benched: {', '.join(deactivated)}")

    @commands.command()
    @dm_only
    async def activateall(self, ctx):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE characters SET active = 1")
        conn.commit(); cur.close(); conn.close()
        await ctx.send("✅ All characters activated.")

    @commands.command()
    @dm_only
    async def deactivateall(self, ctx):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE characters SET active = 0")
        conn.commit(); cur.close(); conn.close()
        await ctx.send("✅ All characters benched.")

    @commands.command()
    async def roster(self, ctx):
        from data.static_data import get_class_title
        chars = load_active_characters()
        if not chars: await ctx.send("No active characters."); return
        embed = discord.Embed(title="⚔️ Active Roster", color=discord.Color.dark_purple())
        for c in chars:
            title = get_class_title(c["class"], c.get("level", 1))
            embed.add_field(name=c["char_name"], value=f"Level {c['level']} {c['race']} {title}", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @dm_only
    async def bench(self, ctx):
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM characters WHERE active = 0 ORDER BY char_name")
        chars = cur.fetchall(); cur.close(); conn.close()
        if not chars: await ctx.send("No benched characters."); return
        embed = discord.Embed(title="🪑 Benched Characters", color=discord.Color.greyple())
        for c in chars:
            embed.add_field(name=c["char_name"], value=f"Level {c['level']} {c['race']} {c['class']}", inline=False)
        await ctx.send(embed=embed)

    # ── DM Player Management ──────────────────────────────────────────────────

    @commands.command()
    @dm_only
    async def dmheal(self, ctx, target, amount: int):
        member_id = None
        if target.startswith("<@") and target.endswith(">"):
            member_id = int(target.strip("<@!>"))
        else:
            from data.db import load_all_characters
            for ch in load_all_characters():
                if ch["char_name"].lower() == target.lower() or target.lower() in ch["char_name"].lower():
                    member_id = ch["discord_id"]; break
        if not member_id:
            await ctx.send(f"❌ No character found: `{target}`"); return
        c = get_db_char(member_id)
        if not c: await ctx.send("No character."); return
        max_hp = c.get("max_hp") or c["hp"]
        new_hp = min(max_hp, c["hp"] + amount)
        set_char_field(member_id, "hp", new_hp)
        await ctx.send(f"💚 DM healed **{c['char_name']}** for **{amount} HP**. HP: **{new_hp}/{max_hp}**")

    @commands.command()
    @dm_only
    async def dmaddxp(self, ctx, member: discord.Member, amount: int):
        c = get_db_char(member.id)
        if not c: return
        new_xp = (c.get("xp") or 0) + amount
        set_char_field(member.id, "xp", new_xp)
        await ctx.send(f"⭐ **{c['char_name']}** gained **{amount} XP** (Total: {new_xp})")
        from data.helpers import check_auto_level
        await check_auto_level(ctx, member.id)

    @commands.command()
    @dm_only
    async def give(self, ctx, target, *, item: str):
        member_id = None
        if target.startswith("<@") and target.endswith(">"):
            member_id = int(target.strip("<@!>"))
        else:
            from data.db import load_all_characters
            for ch in load_all_characters():
                if ch["char_name"].lower() == target.lower() or target.lower() in ch["char_name"].lower():
                    member_id = ch["discord_id"]; break
        if not member_id:
            await ctx.send(f"❌ No character found: `{target}`"); return
        c = get_db_char(member_id)
        if not c: return
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        items.append(item.strip())
        set_char_field(member_id, "inventory", ", ".join(items))
        parts = item.lower().split()
        if len(parts) == 2 and parts[1] in ("gold","gp") and parts[0].isdigit():
            set_char_field(member_id, "gold", (c.get("gold") or 0) + int(parts[0]))
        await ctx.send(f"🎁 **{c['char_name']}** received **{item}**!")

    @commands.command()
    @dm_only
    async def announce(self, ctx, *, message: str):
        embed = discord.Embed(description=f"📣 {message}", color=discord.Color.gold())
        embed.set_author(name="📜 Dungeon Master Announcement")
        await ctx.send(embed=embed)

    @commands.command()
    @dm_only
    async def atmosphere(self, ctx, *, setting: str):
        """Change the voice channel name and text channel topic for immersion.
        Usage: !atmosphere The Hallway | The walls are closing in."""
        parts = setting.split("|", 1)
        vc_name = parts[0].strip()
        topic = parts[1].strip() if len(parts) > 1 else ""
        # Rename the voice channel the DM is in
        if ctx.author.voice and ctx.author.voice.channel:
            try:
                await ctx.author.voice.channel.edit(name=vc_name)
            except: pass
        # Update the text channel topic
        if topic:
            try:
                await ctx.channel.edit(topic=topic)
            except: pass
        await ctx.send(f"🌑 *The atmosphere shifts...*", delete_after=5)

    @commands.command()
    @dm_only
    async def journal(self, ctx, *, entry: str):
        """Post an ambient journal entry to #the-journal channel."""
        journal_ch = discord.utils.get(ctx.guild.text_channels, name="the-journal")
        if not journal_ch:
            await ctx.send("❌ No #the-journal channel found."); return
        embed = discord.Embed(description=f"*{entry}*", color=discord.Color.dark_purple())
        embed.set_author(name="📖 The Journal")
        embed.set_footer(text="The ink is fresh. The handwriting is not yours.")
        await journal_ch.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @commands.command()
    @dm_only
    async def giveinspiration(self, ctx, member: discord.Member):
        set_char_field(member.id, "inspiration", 1)
        c = get_db_char(member.id)
        await ctx.send(f"✨ **{c['char_name']}** has been granted inspiration!")

    @commands.command()
    @dm_only
    async def posthelp(self, ctx):
        """Re-post the command guide in #dnd-help."""
        help_channel = discord.utils.get(ctx.guild.text_channels, name="dnd-help")
        if not help_channel:
            await ctx.send("❌ No #dnd-help channel found."); return
        async for msg in help_channel.history(limit=20):
            if msg.author == self.bot.user:
                await msg.delete()
        e1 = discord.Embed(title="⚔️ Player Commands — Quick Reference", color=discord.Color.dark_purple())
        e1.add_field(name="🎮 Getting Started", value="`!createchar` Create character\n`!createchar random` Random\n`/mychar` Your sheet\n`/party` Active party", inline=False)
        e1.add_field(name="⚔️ Combat", value="`/target <enemy>` Attack\n`/cast <spell> [target] [level]` Cast\n`/usepotion` Health potion\n`/reaction <desc>` Reaction\n`/deathsave` Death save", inline=False)
        e1.add_field(name="🎲 Dice & Checks", value="`/roll <NdX>` Roll dice\n`/save <stat>` Saving throw\n`/check <skill>` Skill check\n`/passive <skill>` Passive score", inline=False)
        e1.add_field(name="❤️ Health & Resting", value="`/hp` View HP\n`/heal <amt>` Heal\n`/shortrest` Short rest\n`/longrest` Long rest\n`/resurrect @player` Scroll", inline=False)
        e2 = discord.Embed(color=discord.Color.dark_purple())
        e2.add_field(name="🎒 Equipment", value="`/inventory` Items\n`/equip <weapon>` Equip\n`/weapon <name>` Stats\n`/ac` View AC\n`/setac <armor>` Set armor", inline=False)
        e2.add_field(name="🔮 Spellcasting", value="`/spellbook` Available spells\n`/learnspell <name>` Learn\n`/myspells` Known\n`/cast <spell> [target]` Cast\n`/spellslots` Slots\n`/spelldc` Save DC", inline=False)
        e2.add_field(name="⚡ Class & Leveling", value="`/resources` Class resources\n`/useresource <name>` Spend\n`/useitem <name>` Activate item\n`/xp` View XP\n`/levelup` Level up\n`/asi <stat>` ASI\n`/feats` View feats\n`/takefeat <name>` Take feat", inline=False)
        e2.add_field(name="💰 Gold & Trading", value="`/gold` Currency\n`/trade @player <item>` Offer\n`/accepttrade` Accept\n`/declinetrade` Decline", inline=False)
        e3 = discord.Embed(color=discord.Color.dark_purple())
        e3.add_field(name="📋 Conditions", value="`/condition <name>` Look up\n`/conditions` List all\n`/exhaustion` View\n`/inspiration` Check\n`/useinspiration` Use", inline=False)
        e3.add_field(name="✨ Attunement", value="`/attune <item>` Attune (max 3)\n`/unattune <item>` End\n`/attuned` View", inline=False)
        e3.add_field(name="📖 Character", value="`/backstory [@player]` Backstory\n`!setbackstory <text>` Write\n`/features` Features\n`/profs` Proficiencies\n`/classes` Classes\n`/races` Races", inline=False)
        e3.set_footer(text="Type / to browse all commands. Type !createchar in #simulacrum-lab-🧪 to begin.")
        await help_channel.send(embed=e1)
        await help_channel.send(embed=e2)
        await help_channel.send(embed=e3)
        await ctx.send("✅ Command guide posted in #dnd-help.", delete_after=5)

    @commands.command()
    @dm_only
    async def testgif(self, ctx, *, path: str = "vfx/character_vfx/level_up.gif"):
        """Test any gif path. Add 'crit' to test _crit variant."""
        import os
        is_crit = path.endswith(" crit")
        if is_crit:
            path = path[:-5].strip()
        from data.static_data import resolve_gif
        resolved = resolve_gif(path, is_crit)
        if resolved:
            label = "✅ CRIT variant" if is_crit and "_crit" in resolved else "✅ Normal"
            await ctx.send(f"{label}: `{resolved}`", file=discord.File(resolved, filename=os.path.basename(resolved)))
        else:
            await ctx.send(f"❌ File not found: `{path}`")

    @commands.command()
    @dm_only
    async def updatechar(self, ctx, *, args: str):
        """DM: Update any field. Usage: !updatechar CharName field value OR !updatechar @player field value"""
        from data.db import get_db
        words = args.split()
        if len(words) < 2:
            await ctx.send("❌ Usage: `!updatechar <name/@mention> <field> [value]`"); return

        # Check if first word is a mention
        if words[0].startswith("<@") and words[0].endswith(">"):
            discord_id = int(words[0].strip("<@!>"))
            field = words[1].lower()
            value = " ".join(words[2:]) if len(words) > 2 else ""
        else:
            # Try progressively longer name matches against DB
            conn = get_db(); cur = conn.cursor(dictionary=True)
            discord_id = None
            split_at = None
            for i in range(1, len(words)):
                candidate = " ".join(words[:i])
                cur.execute("SELECT discord_id FROM characters WHERE LOWER(char_name) = LOWER(%s)", (candidate,))
                row = cur.fetchone()
                if row:
                    discord_id = row["discord_id"]
                    split_at = i
                    break
            cur.close(); conn.close()
            if not discord_id:
                await ctx.send(f"❌ No character found matching any part of `{args}`."); return
            remaining = words[split_at:]
            if not remaining:
                await ctx.send("❌ No field specified."); return
            field = remaining[0].lower()
            value = " ".join(remaining[1:]) if len(remaining) > 1 else ""

        str_fields = {"notes","subclass","backstory","known_spells","inventory","equipped_weapon","conditions_active","dragon_ancestry"}
        if field in str_fields:
            val = value
        else:
            try: val = int(value) if value else 0
            except ValueError: val = value
        if set_char_field(discord_id, field, val):
            c = get_db_char(discord_id)
            await ctx.send(f"✅ **{c['char_name']}** — updated **{field}** to **{val}**.")
        else:
            await ctx.send(f"❌ `{field}` cannot be updated.")

    # ── Void Walk — Legendary Weapon Secret Encounter ──────────────────────────

    @commands.command()
    @dm_only
    async def voidwalk(self, ctx, member: discord.Member):
        """Initiate the Void Walk for a player attempting to find Aldric's Paradox."""
        import os
        c = get_db_char(member.id)
        if not c:
            await ctx.send(f"{member.display_name} has no character."); return

        await ctx.send(f"🕳️ **{c['char_name']}** steps off the path. Into the void. Alone.\n*The darkness swallows them. The party can only watch.*")

        # Save 1: WIS
        await ctx.send(f"**{c['char_name']}** — the void speaks your name. **Wisdom save DC 14.**")
        r1 = random.randint(1, 20)
        wis_mod = modifier(c["wisdom"])
        wis_prof = prof_bonus(c["level"]) if "wisdom" in CLASS_SAVE_PROFS.get(c["class"], set()) else 0
        total1 = r1 + wis_mod + wis_prof
        await ctx.send(f"🎲 WIS save: `{r1}` {mod_str(c['wisdom'])}{f' +{wis_prof}' if wis_prof else ''} = **{total1}**")
        if total1 < 14:
            await self._voidwalk_fail(ctx, member, c); return
        await ctx.send(f"✅ **{c['char_name']}** resists. Pushes deeper. The cold is absolute.")

        # Save 2: CON
        await ctx.send(f"**{c['char_name']}** — your body is failing. There is no air here. **Constitution save DC 14.**")
        r2 = random.randint(1, 20)
        con_mod = modifier(c["constitution"])
        con_prof = prof_bonus(c["level"]) if "constitution" in CLASS_SAVE_PROFS.get(c["class"], set()) else 0
        total2 = r2 + con_mod + con_prof
        await ctx.send(f"🎲 CON save: `{r2}` {mod_str(c['constitution'])}{f' +{con_prof}' if con_prof else ''} = **{total2}**")
        if total2 < 14:
            await self._voidwalk_fail(ctx, member, c); return
        await ctx.send(f"✅ **{c['char_name']}** endures. One more step. Something glints ahead.")

        # Save 3: CHA
        await ctx.send(f"**{c['char_name']}** — the void wants you to forget who you are. **Charisma save DC 14.**")
        r3 = random.randint(1, 20)
        cha_mod = modifier(c["charisma"])
        cha_prof = prof_bonus(c["level"]) if "charisma" in CLASS_SAVE_PROFS.get(c["class"], set()) else 0
        total3 = r3 + cha_mod + cha_prof
        await ctx.send(f"🎲 CHA save: `{r3}` {mod_str(c['charisma'])}{f' +{cha_prof}' if cha_prof else ''} = **{total3}**")
        if total3 < 14:
            await self._voidwalk_fail(ctx, member, c); return

        # SUCCESS
        embed = discord.Embed(title="🟠 Aldric's Paradox", color=discord.Color(0xe67e22))
        embed.add_field(name="Rarity", value="Legendary", inline=True)
        embed.add_field(name="Damage", value="1d4+3 force", inline=True)
        embed.add_field(name="Properties", value="Finesse, light, thrown (20/60 ft). Exists in two states. On hit: WIS DC 15 or displaced 10 ft random direction. 1/long rest: cast Dimension Door (no slot).", inline=False)
        gif_path = "vfx/entity_vfx/aldrics_paradox.gif"
        if os.path.exists(gif_path):
            embed.set_image(url="attachment://aldrics_paradox.gif")
            await ctx.send(
                f"✅✅✅ **{c['char_name']}** pushes through the void.\n\n"
                f"*In the absolute nothing, a camp. A bedroll, stiff with age. A lantern, long dead. "
                f"And embedded in the ground — a dagger. Its blade flickers between existing and not existing. "
                f"The handle is warm. It was waiting.*\n\n"
                f"🟠 **LEGENDARY ITEM FOUND: Aldric's Paradox**",
                embed=embed, file=discord.File(gif_path, filename="aldrics_paradox.gif")
            )
        else:
            await ctx.send(
                f"✅✅✅ **{c['char_name']}** pushes through the void.\n\n"
                f"🟠 **LEGENDARY ITEM FOUND: Aldric's Paradox**",
                embed=embed
            )
        # Add to inventory
        items = [i.strip() for i in (c.get("inventory") or "").split(",") if i.strip()]
        items.append("Aldric's Paradox")
        set_char_field(member.id, "inventory", ", ".join(items))
        await ctx.send(f"*{c['char_name']} stumbles back to the fork. The party sees them emerge from nothing, dagger in hand, eyes wide.*")

    async def _voidwalk_fail(self, ctx, member, c):
        """Handle void walk failure."""
        import random as _rand
        rolls = [_rand.randint(1, 10) for _ in range(4)]
        dmg = sum(rolls)
        new_hp = max(0, c["hp"] - dmg)
        set_char_field(member.id, "hp", new_hp)
        new_dread = (c.get("dread") or 0) + 3
        set_char_field(member.id, "dread", new_dread)
        await ctx.send(
            f"❌ **FAILED.**\n\n"
            f"*The void rejects {c['char_name']}. It tears at their mind — images of nothing, "
            f"of being nothing, of having never existed.*\n\n"
            f"💥 **{dmg} psychic damage** (`[{', '.join(str(r) for r in rolls)}]`). HP: **{new_hp}**\n"
            f"👁️ **+3 Dread** (now {new_dread})\n\n"
            f"*{c['char_name']} crashes back onto the path. Shaking. Silent.*"
        )

    @commands.command(aliases=["lr"])
    @dm_only
    async def longrest_all(self, ctx):
        """Long rest ALL active characters. Restores HP, slots, hit dice, rests."""
        from data.db import load_active_characters, get_db, set_slots
        from data.static_data import get_slots_for_level, CLASS_HP, modifier
        chars = load_active_characters()
        if not chars:
            await ctx.send("❌ No active characters."); return
        conn = get_db(); cur = conn.cursor()
        for c in chars:
            max_hp = c.get("max_hp") or c["hp"]
            restored = max(1, c["level"] // 2)
            new_hd = min(c["level"], (c.get("hit_dice_remaining") or 0) + restored)
            cur.execute("UPDATE characters SET hp=%s, concentration=NULL, hit_dice_remaining=%s WHERE discord_id=%s", (max_hp, new_hd, c["discord_id"]))
            set_slots(c["discord_id"], get_slots_for_level(c["class"], c["level"]))
            set_char_field(c["discord_id"], "racial_uses", 0)
            set_char_field(c["discord_id"], "short_rest_used", 0)
        conn.commit(); cur.close(); conn.close()
        await ctx.send(f"🌙 **Long Rest.** All {len(chars)} characters restored — HP, spell slots, hit dice, and rest charges.")

    @commands.command()
    @dm_only
    async def inflict(self, ctx, member: discord.Member, *, affliction: str):
        """DM: Apply a condition, poison, curse, or disease to a player."""
        from data.static_data import ALL_AFFLICTIONS, POISONS, CURSES, DISEASES
        key = affliction.lower().strip()
        c = get_db_char(member.id)
        if not c: await ctx.send("❌ No character found."); return
        # Validate
        if key not in ALL_AFFLICTIONS:
            await ctx.send(f"❌ Unknown affliction: `{key}`.\nConditions: {', '.join(CONDITION_EFFECTS.keys())}\nPoisons: {', '.join(POISONS.keys())}\nCurses: {', '.join(CURSES.keys())}\nDiseases: {', '.join(DISEASES.keys())}"); return
        # Add to conditions_active
        conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        if key not in conds:
            conds.append(key)
            set_char_field(member.id, "conditions_active", ", ".join(conds))
        # Apply immediate mechanical effects
        info = ALL_AFFLICTIONS[key]
        msg = f"☠️ **{c['char_name']}** is afflicted with **{key.title()}**!"
        if info["category"] == "poison":
            p = POISONS[key]
            dot_str = f" ({p['dot']} {p['dot_type']}/turn, {p['duration']} turns)" if p["dot"] else ""
            msg += f"\n🧪 Poison{dot_str}"
        elif info["category"] == "curse":
            msg += f"\n🔮 Curse: *{CURSES[key]['desc']}*\n💊 Cure: {CURSES[key]['cure']}"
            if key == "curse of frailty":
                new_max = max(1, (c.get("max_hp") or c["hp"]) - 10)
                set_char_field(member.id, "max_hp", new_max)
                if c["hp"] > new_max: set_char_field(member.id, "hp", new_max)
            elif key == "curse of echoes":
                set_char_field(member.id, "ac", max(1, c.get("ac", 10) - 2))
        elif info["category"] == "disease":
            msg += f"\n🦠 Disease: *{DISEASES[key]['desc']}*\n💊 Cure: {DISEASES[key]['cure']}"
        await ctx.send(msg)

    @commands.command()
    @dm_only
    async def cure(self, ctx, member: discord.Member, *, affliction: str = "all"):
        """DM: Remove a condition/poison/curse/disease. Use 'all' to clear everything."""
        c = get_db_char(member.id)
        if not c: await ctx.send("❌ No character found."); return
        from data.static_data import CURSES, BUFFS
        key = affliction.lower().strip()
        conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        if key == "all":
            # Reverse mechanical effects
            ac_reduction = 0
            for cond in conds:
                if cond == "curse of frailty":
                    set_char_field(member.id, "max_hp", (c.get("max_hp") or c["hp"]) + 10)
                elif cond == "curse of echoes":
                    ac_reduction -= 2  # was -2, reversing adds back
                elif cond.startswith("buff:"):
                    buff_key = cond[5:]
                    if buff_key in BUFFS and "ac_plus_2" in BUFFS[buff_key]["mechanical"]:
                        ac_reduction += 2
            if ac_reduction:
                set_char_field(member.id, "ac", c.get("ac", 10) - ac_reduction)
            set_char_field(member.id, "conditions_active", None)
            await ctx.send(f"✨ **{c['char_name']}** — all afflictions cured!")
        else:
            if key not in conds:
                await ctx.send(f"❌ **{c['char_name']}** doesn't have `{key}`."); return
            # Reverse mechanical effects
            if key == "curse of frailty":
                set_char_field(member.id, "max_hp", (c.get("max_hp") or c["hp"]) + 10)
            elif key == "curse of echoes":
                set_char_field(member.id, "ac", c.get("ac", 10) + 2)
            conds = [x for x in conds if x != key]
            set_char_field(member.id, "conditions_active", ", ".join(conds) if conds else None)
            await ctx.send(f"✨ **{c['char_name']}** — **{key.title()}** cured!")

    @commands.command()
    @dm_only
    async def buff(self, ctx, member: discord.Member, *, buff_name: str):
        """DM: Apply a buff to a player."""
        from data.static_data import BUFFS
        key = buff_name.lower().strip()
        c = get_db_char(member.id)
        if not c: await ctx.send("❌ No character found."); return
        if key not in BUFFS:
            await ctx.send(f"❌ Unknown buff: `{key}`.\nAvailable: {', '.join(BUFFS.keys())}"); return
        b = BUFFS[key]
        conds = [x.strip() for x in (c.get("conditions_active") or "").split(",") if x.strip()]
        buff_tag = f"buff:{key}"
        if buff_tag not in conds:
            conds.append(buff_tag)
            set_char_field(member.id, "conditions_active", ", ".join(conds))
        # Apply immediate effects
        if "temp_hp_5" in b["mechanical"]:
            set_char_field(member.id, "temp_hp", max(c.get("temp_hp", 0) or 0, 5))
        if "ac_plus_2" in b["mechanical"]:
            set_char_field(member.id, "ac", c.get("ac", 10) + 2)
        await ctx.send(f"⬆️ **{c['char_name']}** gains **{key.title()}**!\n*{b['desc']}*")

    @commands.command()
    @dm_only
    async def setstats(self, ctx, *, args: str):
        """DM: Manually set a character's ability scores. Usage: !setstats CharName 16 14 12 10 8 13 (STR DEX CON INT WIS CHA)"""
        parts = args.split()
        if len(parts) < 7:
            await ctx.send("❌ Usage: `!setstats CharName STR DEX CON INT WIS CHA`\nExample: `!setstats Athena 16 14 12 10 8 13`"); return
        # Find character name (try progressively longer matches)
        from data.db import get_db
        import json
        conn = get_db(); cur = conn.cursor(dictionary=True)
        discord_id = None
        split_at = None
        for i in range(1, len(parts) - 5):
            candidate = " ".join(parts[:i])
            cur.execute("SELECT discord_id FROM characters WHERE LOWER(char_name) = LOWER(%s)", (candidate,))
            row = cur.fetchone()
            if row:
                discord_id = row["discord_id"]
                split_at = i
                break
        cur.close(); conn.close()
        if not discord_id:
            await ctx.send("❌ Character not found."); return
        stats = parts[split_at:]
        if len(stats) != 6 or not all(s.isdigit() for s in stats):
            await ctx.send("❌ Need exactly 6 numbers: STR DEX CON INT WIS CHA"); return
        str_v, dex_v, con_v, int_v, wis_v, cha_v = [int(s) for s in stats]
        set_char_field(discord_id, "strength", str_v)
        set_char_field(discord_id, "dexterity", dex_v)
        set_char_field(discord_id, "constitution", con_v)
        set_char_field(discord_id, "intelligence", int_v)
        set_char_field(discord_id, "wisdom", wis_v)
        set_char_field(discord_id, "charisma", cha_v)
        # Also save as original_stats
        scores = {"Strength": str_v, "Dexterity": dex_v, "Constitution": con_v, "Intelligence": int_v, "Wisdom": wis_v, "Charisma": cha_v}
        set_char_field(discord_id, "original_stats", json.dumps(scores))
        c = get_db_char(discord_id)
        await ctx.send(f"✅ **{c['char_name']}** stats set: STR {str_v} DEX {dex_v} CON {con_v} INT {int_v} WIS {wis_v} CHA {cha_v}\n📌 Saved as original stats.")

    @commands.command()
    @dm_only
    async def resetchar(self, ctx, *, char_name: str):
        """DM: Factory reset a character to level 1. Keeps name, race, class, subclass, backstory."""
        from data.db import get_db
        from data.static_data import CLASS_HP, roll_ability_scores, get_slots_for_level
        import json
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM characters WHERE LOWER(char_name) = LOWER(%s)", (char_name,))
        c = cur.fetchone()
        if not c:
            cur.close(); conn.close()
            await ctx.send(f"❌ No character named `{char_name}`."); return
        # Restore original stats if saved, otherwise SAVE CURRENT stats as originals (never reroll)
        if c.get("original_stats"):
            scores = json.loads(c["original_stats"])
            stats_note = "Original stats restored."
        else:
            # Grandfather: save their CURRENT stats as the originals
            scores = {
                "Strength": c["strength"], "Dexterity": c["dexterity"],
                "Constitution": c["constitution"], "Intelligence": c["intelligence"],
                "Wisdom": c["wisdom"], "Charisma": c["charisma"]
            }
            set_char_field(c["discord_id"], "original_stats", json.dumps(scores))
            stats_note = "Current stats saved as originals."
        hit_die = CLASS_HP.get(c["class"], 8)
        hp = hit_die + (scores["Constitution"] - 10) // 2
        ac = 10 + (scores["Dexterity"] - 10) // 2
        cur.execute("""UPDATE characters SET
            level=1, xp=0, hp=%s, max_hp=%s, ac=%s,
            strength=%s, dexterity=%s, constitution=%s, intelligence=%s, wisdom=%s, charisma=%s,
            equipped_weapon=NULL, equipped_armor=NULL, equipped_offhand=NULL,
            equipped_head=NULL, equipped_hands=NULL, equipped_feet=NULL, equipped_ring=NULL,
            inventory=NULL, gold=0, pp=0, sp=0, cp=0,
            known_spells=NULL, concentration=NULL, conditions_active=NULL,
            hit_dice_remaining=1, temp_hp=0, exhaustion=0, dread=0,
            inspiration=0, racial_uses=0, short_rest_used=0, long_rest_used=0,
            feats=NULL, attuned_items=NULL, class_resources=NULL
            WHERE discord_id=%s""",
            (hp, hp, ac,
             scores["Strength"], scores["Dexterity"], scores["Constitution"],
             scores["Intelligence"], scores["Wisdom"], scores["Charisma"],
             c["discord_id"]))
        conn.commit(); cur.close(); conn.close()
        from data.db import set_slots
        set_slots(c["discord_id"], get_slots_for_level(c["class"], 1))
        # Re-apply starting equipment
        from _config import AUTO_STARTING_EQUIPMENT
        from data.static_data import CLASS_STARTING_EQUIPMENT, ARMOR_TABLE, LIGHT_ARMOR, MEDIUM_ARMOR, modifier as _mod
        if AUTO_STARTING_EQUIPMENT and c["class"] in CLASS_STARTING_EQUIPMENT:
            weapon_key, armor_key, has_shield, items = CLASS_STARTING_EQUIPMENT[c["class"]]
            set_char_field(c["discord_id"], "equipped_weapon", weapon_key)
            set_char_field(c["discord_id"], "inventory", ", ".join(items))
            # Recalculate AC with armor
            dex_mod = (scores["Dexterity"] - 10) // 2
            base_ac = ARMOR_TABLE.get(armor_key, 10)
            if armor_key in LIGHT_ARMOR or armor_key == "no armor": calc_ac = base_ac + dex_mod
            elif armor_key in MEDIUM_ARMOR: calc_ac = base_ac + min(dex_mod, 2)
            else: calc_ac = base_ac
            if has_shield: calc_ac += 2
            set_char_field(c["discord_id"], "ac", calc_ac)
            if armor_key != "no armor":
                set_char_field(c["discord_id"], "equipped_armor", armor_key)
        await ctx.send(f"♻️ **{c['char_name']}** factory reset to Level 1. {stats_note} Starting equipment restored. Backstory preserved.")

    @commands.command()
    @dm_only
    async def dmdeletechar(self, ctx, *, char_name: str):
        """Delete any character by name from the database."""
        from data.db import get_db
        conn = get_db(); cur = conn.cursor()
        cur.execute("DELETE FROM characters WHERE char_name = %s", (char_name,))
        deleted = cur.rowcount
        conn.commit(); cur.close(); conn.close()
        if deleted:
            await ctx.send(f"🗑️ **{char_name}** deleted from database.")
        else:
            await ctx.send(f"❌ No character named `{char_name}` found.")

    @commands.command()
    @dm_only
    async def roster(self, ctx):
        """Show ALL characters in the database."""
        from data.db import get_db
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT discord_name, char_name, race, class, level, hp, max_hp FROM characters ORDER BY level DESC")
        rows = cur.fetchall(); cur.close(); conn.close()
        if not rows:
            await ctx.send("❌ No characters in database."); return
        embed = discord.Embed(title=f"📋 Full Roster ({len(rows)} characters)", color=discord.Color.dark_teal())
        lines = []
        for r in rows:
            hp_str = f"{r['hp']}/{r['max_hp']}" if r.get('max_hp') else f"{r['hp']}"
            lines.append(f"**{r['char_name']}** — {r['race']} {r['class']} Lv{r['level']} | HP: {hp_str} | *{r['discord_name']}*")
        embed.description = "\n".join(lines[:25])
        if len(rows) > 25:
            embed.set_footer(text=f"Showing 25/{len(rows)}")
        await ctx.send(embed=embed)

    @commands.command()
    @dm_only
    async def resetrests(self, ctx, member: discord.Member = None):
        """Reset rest charges for a player or all players."""
        from data.db import load_active_characters
        if member:
            set_char_field(member.id, "short_rest_used", 0)
            set_char_field(member.id, "long_rest_used", 0)
            await ctx.send(f"♻️ Rest charges reset for {member.display_name}.")
        else:
            chars = load_active_characters()
            for c in chars:
                set_char_field(c["discord_id"], "short_rest_used", 0)
                set_char_field(c["discord_id"], "long_rest_used", 0)
            await ctx.send(f"♻️ Rest charges reset for **{len(chars)}** players.")

async def setup(bot):
    await bot.add_cog(DMTools(bot))
