from datetime import datetime

import discord
import pytz
from discord.ext import commands

from utils.commons import DISPLAY_DATE_TIME_FORMAT
from utils.logger import init_logger

NAME_LIST_TITLE = 'Wolfie Name List'

logger = init_logger('WolfiePreferences')

EMOJIS = {"day": "☀️", "night": "💤"}

class Preferences(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wolfie.set', aliases=['wolfie.set.prefs', 'wolfie.prefs', 'wolfie.me'])
    async def set_name(self, ctx,
                       alias: str = commands.parameter(description="- your in-game name"),
                       timezone: str = commands.parameter(description="- your local timezone", default='UTC')):
        """
        Tell Wolfie your name and timezone.
        Find timezone here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """
        embed = discord.Embed(title=NAME_LIST_TITLE,
                              color=discord.Color.dark_embed())

        pref = await self.bot.memory.get_prefs(str(ctx.author.id), {})
        if pref.get('alias') != alias:
            pref.update({
                'name': ctx.author.display_name,
                'alias': alias,
                'timezone': timezone
            })
            await self.bot.memory.update_prefs(str(ctx.author.id), pref)
            embed.add_field(name=f"{ctx.author.name}", value=f"is known to wolfie as {alias}", inline=False)
            await self.bot.memory.save_prefs()
        else:
            await ctx.send("Wolfie already knows your name")
            return

        await ctx.send(embed=embed)


    @commands.command(name="wolfie.set.time",  aliases=['wolfie.time'])
    async def set_timezone(self, ctx, timezone_name: str=commands.parameter(description="- your local timezone")):
            """
            Tell Wolfie your local timezone. Wolfie use your local timezone when display info requested by you.
            Defaults to UTC. Find timezone here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
            """
            try:
                zone:str = pytz.timezone(timezone_name).zone  # Validate timezone

                pref = await self.bot.memory.get_prefs(str(ctx.author.id), {})
                pref.update({
                    'name': ctx.author.display_name,
                    'timezone' : zone
                })
                await self.bot.memory.update_prefs(str(ctx.author.id), pref)
                await self.bot.memory.save_prefs()

                await ctx.send(f"Timezone set to {zone}.")
            except pytz.UnknownTimeZoneError:
                await ctx.send("Invalid timezone. Please provide a valid timezone name.")


    @commands.command(name='wolfie.list', aliases=['wolfie.ls'])
    async def list_prefs(self, ctx):
        """Display what Wolfie knows about you."""

        embed = discord.Embed(title=NAME_LIST_TITLE, color=discord.Color.dark_embed())
        now = datetime.now()
        all_prefs = await self.bot.memory.get_prefs_all()
        for i, value in enumerate(all_prefs.values(), start=1):

            tz = value.get('timezone') or 'UTC'
            user_timezone = pytz.timezone(tz)
            user_datetime = now.astimezone(user_timezone)
            # TODO use preferred hours
            day_night = EMOJIS['day'] if 6 < user_datetime.hour < 18 else EMOJIS['night']
            details = f"{day_night}️ {now.astimezone(user_timezone).strftime(DISPLAY_DATE_TIME_FORMAT)}"

            embed.add_field(
                name=f"{i}. {value.get('alias')}-{value.get('timezone')}",
                value=details, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Preferences(bot))