import discord
from discord.ext import commands
from _config import COMMAND_PREFIX, BOT_TOKEN, CHANNEL_RESTRICTIONS
from data.db import init_db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
bot.remove_command("help")

@bot.check
async def check_channel_restriction(ctx):
    cmd_name = ctx.command.name if ctx.command else None
    if cmd_name and cmd_name in CHANNEL_RESTRICTIONS:
        required_channel = CHANNEL_RESTRICTIONS[cmd_name]
        if ctx.channel.name != required_channel:
            await ctx.send(f"❌ Use `!{cmd_name}` in **#{required_channel}**.", delete_after=5)
            return False
    return True

COGS = [
    "cogs.combat",
    "cogs.characters",
    "cogs.spells",
    "cogs.inventory",
    "cogs.leveling",
    "cogs.conditions",
    "cogs.dm_tools",
]

@bot.event
async def on_ready():
    init_db()
    for cog in COGS:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            print(f"Failed to load {cog}: {e}")
    print(f"Logged in as {bot.user} — {len(COGS)} cogs loaded.")

bot.run(BOT_TOKEN)
