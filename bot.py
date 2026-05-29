import os
import asyncio
import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime

import scraper
import version_store

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")


def make_embed(release: dict, is_new: bool) -> discord.Embed:
    color = discord.Color.green() if is_new else discord.Color.blurple()
    title = "New Roblox Android Update Detected!" if is_new else "Current Roblox Android Version"
    embed = discord.Embed(
        title=title,
        url=release["url"],
        color=color,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Version", value=f"`{release['version']}`", inline=True)
    embed.add_field(name="Type", value=release["type"].capitalize(), inline=True)
    if release.get("date"):
        embed.add_field(name="Published", value=release["date"], inline=True)
    embed.add_field(name="APKMirror Page", value=f"[View on APKMirror]({release['url']})", inline=False)
    embed.set_footer(text="Roblox Version Tracker • apkmirror.com")
    return embed


class RobloxTracker(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        self.check_roblox_version.start()
        print("[Bot] Slash commands synced. Background version checker started.")

    async def on_ready(self):
        print(f"[Bot] Logged in as {self.user} ({self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Roblox Android releases"
            )
        )

    @tasks.loop(seconds=60)
    async def check_roblox_version(self):
        interval = version_store.get_check_interval()
        # Only check on multiples of 60s matching the interval
        elapsed = self.check_roblox_version.current_loop * 60
        if elapsed % interval != 0 or elapsed == 0:
            return

        channel_id = version_store.get_tracked_channel()
        if not channel_id:
            return

        channel = self.get_channel(channel_id)
        if not channel:
            return

        release = await asyncio.to_thread(scraper.fetch_latest_release)
        if not release:
            print("[Checker] Failed to fetch release info.")
            return

        known = version_store.get_known_version()
        if release["version"] != known:
            version_store.set_known_version(release["version"])
            embed = make_embed(release, is_new=True)
            try:
                await channel.send(embed=embed)
                print(f"[Checker] New version posted: {release['version']}")
            except discord.DiscordException as e:
                print(f"[Checker] Failed to send message: {e}")
        else:
            print(f"[Checker] No new version. Current: {release['version']}")

    @check_roblox_version.before_loop
    async def before_check(self):
        await self.wait_until_ready()
        # Skip the very first tick (elapsed=0 check above handles this)
        await asyncio.sleep(60)


client = RobloxTracker()


@client.tree.command(name="setchannel", description="Set the channel where Roblox version updates will be posted.")
@app_commands.describe(channel="The channel to post updates in (defaults to current channel)")
@app_commands.default_permissions(manage_channels=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target = channel or interaction.channel
    version_store.set_tracked_channel(target.id)
    await interaction.response.send_message(f"Version update announcements will be sent to {target.mention}.")


@client.tree.command(name="checkversion", description="Manually check the current Roblox Android version on APKMirror.")
async def checkversion(interaction: discord.Interaction):
    await interaction.response.defer()
    release = await asyncio.to_thread(scraper.fetch_latest_release)
    if not release:
        await interaction.followup.send("Could not fetch version info from APKMirror. Try again later.")
        return
    embed = make_embed(release, is_new=False)
    await interaction.followup.send(embed=embed)


@client.tree.command(name="setinterval", description="Set how often (in seconds) the bot checks for updates.")
@app_commands.describe(seconds="Check interval in seconds (minimum 60, default 300)")
@app_commands.default_permissions(manage_guild=True)
async def setinterval(interaction: discord.Interaction, seconds: int):
    if seconds < 60:
        await interaction.response.send_message("Minimum check interval is 60 seconds.", ephemeral=True)
        return
    version_store.set_check_interval(seconds)
    mins = seconds // 60
    await interaction.response.send_message(f"Check interval updated to {seconds}s ({mins} min).")


@client.tree.command(name="status", description="Show current tracker status.")
async def status(interaction: discord.Interaction):
    channel_id = version_store.get_tracked_channel()
    known_version = version_store.get_known_version()
    interval = version_store.get_check_interval()

    channel_mention = f"<#{channel_id}>" if channel_id else "Not set — use /setchannel"
    version_str = known_version if known_version else "Not checked yet"

    embed = discord.Embed(title="Roblox Version Tracker Status", color=discord.Color.blurple())
    embed.add_field(name="Announcement Channel", value=channel_mention, inline=False)
    embed.add_field(name="Last Known Version", value=f"`{version_str}`", inline=True)
    embed.add_field(name="Check Interval", value=f"{interval}s ({interval // 60}m)", inline=True)
    embed.set_footer(text="Source: apkmirror.com/apk/roblox-corporation/roblox/")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="help", description="Show all available tracker commands.")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Roblox Version Tracker — Commands",
        color=discord.Color.blurple(),
        description="Tracks Roblox Android releases from APKMirror and announces new versions."
    )
    embed.add_field(name="/setchannel [channel]", value="Set the channel for update announcements.", inline=False)
    embed.add_field(name="/checkversion", value="Manually fetch and display the latest Roblox Android version.", inline=False)
    embed.add_field(name="/setinterval <seconds>", value="Change how often the bot checks for updates (min 60s, default 300s).", inline=False)
    embed.add_field(name="/status", value="Show tracker status: channel, last version, check interval.", inline=False)
    embed.set_footer(text="Source: apkmirror.com/apk/roblox-corporation/roblox/")
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("[Error] DISCORD_TOKEN environment variable is not set.")
        exit(1)
    client.run(DISCORD_TOKEN)
