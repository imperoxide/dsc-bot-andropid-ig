# Roblox Android Version Tracker Bot

A Discord bot that monitors APKMirror for new Roblox Android releases and announces them to a configured channel.

## Overview

- Scrapes `apkmirror.com/apk/roblox-corporation/roblox/` on a configurable interval
- Posts rich embed messages to a Discord channel when a new version is detected
- Stores state in `version_data.json` (last known version, channel ID, check interval)

## Files

- `bot.py` — Discord bot, commands, background checker loop
- `scraper.py` — APKMirror HTML scraping logic
- `version_store.py` — Simple JSON-backed persistence

## Setup

1. Add a `DISCORD_TOKEN` secret with your bot token
2. Run the bot via the workflow
3. In Discord, use `!setchannel` to set the announcement channel

## Commands

| Command | Description |
|---|---|
| `!setchannel [#channel]` | Set where version updates are posted |
| `!checkversion` | Manually check the current Roblox version |
| `!setinterval <seconds>` | Change check frequency (min 60s) |
| `!status` | Show current tracker status |
| `!help_tracker` | List all commands |

## User Preferences

- Python bot using discord.py
- No database — uses local JSON file for persistence
