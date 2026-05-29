import os
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime

import scraper
import version_store

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEFAULT_CHECK_INTERVAL = 300  # 5 minutes


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
    embed.set_thumbnail(url="https://www.apkmirror.com/wp-content/themes/APKMirror/favicon.ico")
    return embed


class RobloxTracker(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.check_roblox_version.start()
        print("[Bot] Background version checker started.")

    async def on_ready(self):
        print(f"[Bot] Logged in as {self.user} ({self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Roblox Android releases"
            )
        )

    @tasks.loop(seconds=1)
    async def check_roblox_version(self):
        interval = version_store.get_check_interval()
        await asyncio.sleep(interval)

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


bot = RobloxTracker()


@bot.command(name="setchannel")
@commands.has_permissions(manage_channels=True)
async def set_channel(ctx, channel: discord.TextChannel = None):
    """Set the channel where version updates will be posted."""
    target = channel or ctx.channel
    version_store.set_tracked_channel(target.id)
    await ctx.reply(f"Version update announcements will be sent to {target.mention}.")


@bot.command(name="checkversion")
async def check_version(ctx):
    """Manually check the current Roblox Android version."""
    async with ctx.typing():
        release = await asyncio.to_thread(scraper.fetch_latest_release)
    if not release:
        await ctx.reply("Could not fetch version info from APKMirror. Try again later.")
        return
    embed = make_embed(release, is_new=False)
    await ctx.reply(embed=embed)


@bot.command(name="setinterval")
@commands.has_permissions(manage_guild=True)
async def set_interval(ctx, seconds: int):
    """Set how often (in seconds) the bot checks for updates. Minimum 60s."""
    if seconds < 60:
        await ctx.reply("Minimum check interval is 60 seconds.")
        return
    version_store.set_check_interval(seconds)
    mins = seconds // 60
    await ctx.reply(f"Check interval updated to {seconds}s ({mins} min).")


@bot.command(name="status")
async def status(ctx):
    """Show current tracker status."""
    channel_id = version_store.get_tracked_channel()
    known_version = version_store.get_known_version()
    interval = version_store.get_check_interval()

    channel_mention = f"<#{channel_id}>" if channel_id else "Not set"
    version_str = known_version if known_version else "Not checked yet"

    embed = discord.Embed(title="Roblox Version Tracker Status", color=discord.Color.blurple())
    embed.add_field(name="Announcement Channel", value=channel_mention, inline=False)
    embed.add_field(name="Last Known Version", value=f"`{version_str}`", inline=True)
    embed.add_field(name="Check Interval", value=f"{interval}s ({interval // 60}m)", inline=True)
    await ctx.reply(embed=embed)


@bot.command(name="help_tracker")
async def help_tracker(ctx):
    """Show all available commands."""
    embed = discord.Embed(
        title="Roblox Version Tracker — Commands",
        color=discord.Color.blurple(),
        description="Tracks Roblox Android releases from APKMirror."
    )
    embed.add_field(name="!setchannel [#channel]", value="Set the channel for update announcements. Defaults to current channel.", inline=False)
    embed.add_field(name="!checkversion", value="Manually fetch and display the latest Roblox Android version.", inline=False)
    embed.add_field(name="!setinterval <seconds>", value="Change how often the bot checks for updates (min 60s, default 300s).", inline=False)
    embed.add_field(name="!status", value="Show tracker status (channel, last version, interval).", inline=False)
    embed.set_footer(text="Source: apkmirror.com/apk/roblox-corporation/roblox/")
    await ctx.reply(embed=embed)


@set_channel.error
@set_interval.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission to use that command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("Invalid argument. Please check the command usage with `!help_tracker`.")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("[Error] DISCORD_TOKEN environment variable is not set.")
        exit(1)
    bot.run(DISCORD_TOKEN)
