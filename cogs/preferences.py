from datetime import datetime, timezone

import discord
import pytz
from discord.ext import commands

from core.cortex import Cortex
from core.ganglia import Memory
from utils.datetime_utils import DISPLAY_DATE_TIME_FORMAT
from utils.logger import init_logger

NAME_LIST_TITLE = 'Wolfie Name List'

logger = init_logger('WolfiePreferences')

EMOJIS = {"day": "☀️", "night": "💤"}

class Preferences(commands.Cog):
    def __init__(self, bot):
        self.cortex: Cortex = bot.cortex
        self.memory = Memory.PREFERENCES

    @commands.command(name='wolfie.set', aliases=['wolfie.set.prefs', 'wolfie.prefs', 'wolfie.me'])
    async def set_name(self, ctx,
                       alias: str = commands.parameter(description="- your in-game name"),
                       tz: str = commands.parameter(description="- your local timezone", default='UTC')):
        """
        Tell Wolfie your name and timezone.
        Find timezone here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """

        # Validate parameters
        if not alias:
            await ctx.send("Please provide an alias.")
            return
        try:
            tz = pytz.timezone(tz).zone
        except pytz.UnknownTimeZoneError:
            logger.error(f"Invalid timezone: {tz}")
            ctx.send("Invalid timezone. Please provide a valid timezone id.")
            return

        # Prepare the preference data
        user_id = str(ctx.author.id)
        pref = await self.cortex.get_preferences(ctx)
        new_pref = {
            'name': ctx.author.display_name,
            'alias': alias,
            'timezone': tz
        }

        # Perform the update
        if any(pref.get(k) != v for k, v in new_pref.items()):
            pref.update(new_pref)
            await self.cortex.update_memory(Memory.PREFERENCES, user_id, pref)
            embed = discord.Embed(title=NAME_LIST_TITLE,
                              color=discord.Color.dark_embed())
            embed.add_field(name=f"{ctx.author.name}", value=f"is known to wolfie as {alias}", inline=False)
            await self.cortex.remember(self.memory)
        else:
            logger.info("preferences not changed")
            await ctx.send("Wolfie already knows your name")
            return

        logger.info(f"preferences updated for {ctx.author.name}")
        await ctx.send(embed=embed)


    @commands.command(name="wolfie.set.timezone",  aliases=['wolfie.set.tz', 'wolfie.tz'])
    async def set_timezone(self, ctx, timezone_name: str=commands.parameter(description="- your local timezone")):
            """
            Tell Wolfie your local timezone. Wolfie use your local timezone when display info requested by you.
            Defaults to UTC. Find timezone here: (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
            """
            try:
                zone:str = pytz.timezone(timezone_name).zone  # Validate timezone

                pref = await self.cortex.get_preferences(ctx)
                pref.update({
                    'name': ctx.author.display_name,
                    'timezone' : zone
                })
                await self.cortex.update_memory(Memory.PREFERENCES, str(ctx.author.id), pref)
                await self.cortex.remember(self.memory)

                await ctx.send(f"Timezone set to {zone}.")
            except pytz.UnknownTimeZoneError:
                await ctx.send("Invalid timezone. Please provide a valid timezone name.")


    @commands.command(name='wolfie.list', aliases=['wolfie.ls'])
    async def list_preferences(self, ctx):
        """Display what Wolfie knows about everyone."""

        # Retrieve all preferences and format into a list of embed fields
        now = datetime.now()
        embed = discord.Embed(title=NAME_LIST_TITLE, color=discord.Color.dark_embed())
        all_prefs = await self.cortex.get_memory(Memory.PREFERENCES)
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