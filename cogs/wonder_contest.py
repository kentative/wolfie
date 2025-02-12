from datetime import datetime, timedelta, timezone

import discord
import pytz
from discord.ext import commands

from core.memory import get_timezone, get_alias, get_pref

time_mapping = {"t1": "01:00 UTC", "t2": "11:00 UTC", "t3": "17:00 UTC"}
DATE_DISPLAY_FORMAT = '%m-%d %H:%M %Z'

def get_weekend_dates(user_tz):
    """Returns the dates for the upcoming Saturday (d1) and Sunday (d2) in the user's local timezone."""
    today = datetime.now(timezone.utc)
    saturday = today + timedelta(days=(5 - today.weekday()) % 7)
    sunday = saturday + timedelta(days=1)

    user_timezone = pytz.timezone(user_tz)
    saturday_local = saturday.astimezone(user_timezone)
    sunday_local = sunday.astimezone(user_timezone)
    return saturday_local.strftime('%m-%d'), sunday_local.strftime('%m-%d')

def convert_utc_to_local(user_tz: str, utc_date_time: str) -> datetime:
    """Converts a UTC time string (HH:MM UTC) to the user's local timezone."""
    user_timezone = pytz.timezone(user_tz)
    current_year = datetime.now().year
    utc_dt = datetime.strptime(
        f'{current_year}-{utc_date_time}',
        "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)

    return utc_dt.astimezone(user_timezone)

def convert_timeslot_to_utc(day_slot: str, time_slot: str) -> str:
    """Returns "%m-%d %H:%M UTC" from a d1, t1 and timezone"""
    d1_date, d2_date = get_weekend_dates('UTC')
    date_mapping = {"d1": d1_date, "d2": d2_date}
    return f'{date_mapping.get(day_slot)} {time_mapping.get(time_slot)}'

class WonderContest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.teams = {  # Dictionary to store team registrations
            "d1": {"t1": [], "t2": [], "t3": []},
            "d2": {"t1": [], "t2": [], "t3": []}
        }
        self.max_team_size = 30

    @commands.command(name="wonder.add", aliases=['w.add'])
    async def wonder(self, ctx, day: str, time: str):
        """Register user for a specific day and time slot."""
        day = day.lower()
        time = time.lower()

        if day not in self.teams or time not in self.teams[day]:
            await ctx.send("Invalid day or time slot. Use d1/d2 and t1/t2/t3.")
            return

        team = self.teams[day][time]
        user_id = ctx.author.id

        if user_id in team:
            await ctx.send(f"{get_alias(ctx)}, you are already registered for this slot!")
            return

        if len(team) >= self.max_team_size:
            await ctx.send(f"This time slot is full ({self.max_team_size} players max). Try another slot.")
            return

        team.append(user_id)
        user_tz = get_timezone(ctx)
        utc_datetime = convert_timeslot_to_utc(day, time)
        local_time = convert_utc_to_local(user_tz, utc_datetime)
        await ctx.send(f"{get_alias(ctx)} has been registered for {local_time.strftime(DATE_DISPLAY_FORMAT)}")


    @commands.command(name="wonder.ls", aliases=['w.ls'])
    async def wonder_list(self, ctx):
        """List current registration information in UTC."""
        d1_date, d2_date = get_weekend_dates('UTC')
        day_mapping = {"d1": d1_date, "d2": d2_date}

        embed = discord.Embed(title="Wonder Contest Registration", color=discord.Color.dark_gold())

        for day, slots in self.teams.items():
            for time, members in slots.items():
                utc_time = time_mapping[time]
                utc_date = day_mapping[day]

                member_details = []
                for m in members:
                    user_pref = get_pref(m)
                    user_tz = user_pref.get('timezone', 'UTC')
                    user_datetime = convert_utc_to_local(user_tz, f'{utc_date} {utc_time}')
                    member_details.append(
                        f'{user_pref.get("alias")} ({user_datetime.strftime(DATE_DISPLAY_FORMAT)})')

                embed.add_field(name=f"Day {day[1]} ({utc_date}) Slot {time[1]} ({utc_time})",
                                value=f"{', '.join(member_details) if members else 'No registrations'}",
                                inline=False)

        await ctx.send(embed=embed)


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(WonderContest(bot))
