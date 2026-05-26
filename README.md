# LorewalkerDiscordModeratorBot — D&D 5e Discord Bot

A fully automated D&D 5e campaign management bot for Discord. Run combat encounters, cast spells, manage inventory, track conditions, and level up — all through Discord commands.

## Features

- **Automated Combat** — Initiative tracking, auto-advance turns, 60s player timer, enemy AI attacks
- **84 Spells** — Faithful to 5e, per-class spell lists, slot management, Warlock pact magic
- **35 Enemies** — Full bestiary with unique abilities, loot tables, and on-hit conditions
- **Buff/Debuff System** — Mechanical effects (disadvantage, DOT, stun skip, resistance)
- **Weapon & Armor System** — Equipment slots, proficiency checks, bonus damage, on-crit effects
- **Loot System** — Need/Greed rolls, auto-distribution, rarity tiers
- **Racial Abilities** — Dragonborn Breath, Halfling Lucky, Half-Orc Relentless Endurance
- **DM Tools** — Spawn enemies, inflict conditions, whisper players, atmosphere commands
- **Leveling** — XP tracking, ASI, feats, multiclass support

## Quick Start

1. Create a Discord bot at [discord.com/developers](https://discord.com/developers/applications)
2. Enable **Message Content Intent** and **Server Members Intent**
3. Clone this repo
4. Copy `_config.py` and fill in your bot token + MySQL credentials
5. Install dependencies: `pip install -r requirements.txt`
6. Set up MySQL and run the bot: `python _bot.py`

## Requirements

- Python 3.9+
- MySQL database
- Discord bot with Message Content + Members intents

## Commands

### Player Commands
| Command | Description |
|---------|-------------|
| `!createchar` | Create a new character (guided or random) |
| `!target <enemy>` | Attack an enemy on your turn |
| `!cast <spell>` | Cast a spell |
| `!equip <item>` | Equip a weapon or armor |
| `!inventory` | View your inventory |
| `!rest` | Short rest |
| `!lr` | Long rest |

### DM Commands
| Command | Description |
|---------|-------------|
| `!f` | Start combat (initiative phase) |
| `!sp <enemy>` | Spawn an enemy |
| `!g` | Begin combat rounds |
| `!skip` | Skip current player's turn |
| `!q` | End combat |
| `!inflict @player <condition>` | Apply a condition |
| `!buff @player <buff>` | Apply a buff |
| `!give @player <item>` | Give an item |
| `!dmheal @player <amount>` | Heal a player |
| `!roster` | View all characters |

## Project Structure

```
├── _bot.py              ← Entry point
├── _config.py           ← Configuration (tokens, DB, settings)
├── requirements.txt
├── data/
│   ├── static_data.py   ← All game data (spells, enemies, weapons, armor)
│   ├── db.py            ← MySQL database helpers
│   └── helpers.py       ← Shared utilities
├── cogs/
│   ├── combat.py        ← Combat system
│   ├── characters.py    ← Character creation & management
│   ├── spells.py        ← Spell casting
│   ├── inventory.py     ← Equipment & items
│   ├── leveling.py      ← XP & level up
│   ├── conditions.py    ← Saves, checks, rests
│   └── dm_tools.py      ← DM-only commands
```

## License

MIT — see [LICENSE](LICENSE)

## Premium Version

A hosted SaaS version with a web-based DM command center, real-time character dashboards, and multi-tenant support is available at [DNDLorewalkerService](https://dndlorewalker.com) (coming soon).
