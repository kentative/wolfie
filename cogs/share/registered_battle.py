import json
import os

import discord
from discord.ext import commands

from core.memory import get_timezone, get_alias, get_prefs
from utils.logger import init_logger
from utils.timeslot import convert_timeslot_to_utc, convert_utc_to_local, DATE_DISPLAY_FORMAT, get_weekend_dates, \
    time_mapping

logger = init_logger('RegisteredBattle')

class RegisteredBattle(commands.Cog):
    def __init__(self, title: str, file: str, bot):
        self.battle_title = title
        self.data_file = file
        self.bot = bot
        self.teams = {  # Dictionary to store team registrations
            "d1": {"t1": {}, "t2": {}, "t3": {}},
            "d2": {"t1": {}, "t2": {}, "t3": {}}
        }
        self.max_team_size = 30
        self.load_teams()

    def load_teams(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.teams.update(json.load(f))

    def save_teams(self):
        with open(self.data_file, "w") as f:
            json.dump(self.teams, f, indent=4)

    async def register(self, ctx,
                       day: str = commands.parameter(description="use d1 or d2"),
                       time: str = commands.parameter(description="use t1, t2 or t3"),
                       **context):
        """Register user for a specific day and time slot."""
        day = day.lower()
        time = time.lower()

        if day not in self.teams or time not in self.teams[day]:
            await ctx.send("Invalid day or time slot. Use d1/d2 and t1/t2/t3.")
            return

        team: dict = self.teams[day][time]
        user_id = str(ctx.author.id)  # Ensure user_id is stored as a string for JSON compatibility

        if user_id in team:
            await ctx.send("Updating your entry for this slot!")
            team[user_id]["context"].update(context)  # Update existing entry instead of overwriting

        else:
            if len(team) >= self.max_team_size:
                await ctx.send(f"This time slot is full ({self.max_team_size} players max). Try another slot.")
                return

            # Create new entry
            team[user_id] = {"context": context}

        self.save_teams()

        user_tz = get_timezone(ctx)
        utc_datetime = convert_timeslot_to_utc(day, time)
        local_time = convert_utc_to_local(user_tz, utc_datetime)
        await ctx.send(f"{get_alias(ctx)} has been registered for {local_time.strftime(DATE_DISPLAY_FORMAT)}")

    async def unregister(self, ctx,
                     day: str = commands.parameter(description="use d1 or d2"),
                     time: str = commands.parameter(description="use t1, t2 or t3")):
        """Remove user from a specific day and time slot."""
        day = day.lower()
        time = time.lower()

        if day not in self.teams or time not in self.teams[day]:
            await ctx.send("Invalid day or time slot. Use d1/d2 and t1/t2/t3.")
            return

        team: dict = self.teams[day][time]
        user_id = str(ctx.author.id)

        if user_id in team:
            del team[user_id]  # Remove the user from the time slot
            self.save_teams()
            logger.info("Successfully removed.")
            await ctx.send(f"{get_alias(ctx)} has been removed from {day.upper()} {time.upper()}.")
        else:
            logger.warn("Not registered for this time slot.")
            await ctx.send("You are not registered for this time slot.")

    async def list_registration(self, ctx,
                                options: str = commands.parameter(description="supported options: 'all'", default=""),
                                format_member_details: callable = lambda x: x):
        """List current registration information in UTC."""
        d1_date, d2_date = get_weekend_dates('UTC')
        day_mapping = {"d1": d1_date, "d2": d2_date}

        embed = discord.Embed(title=self.battle_title, color=discord.Color.dark_gold())
        for day, slots in self.teams.items():
            for time, members in slots.items():
                logger.info(f"Listing entries for {day} {slots}")
                utc_time = time_mapping[time]
                utc_date = day_mapping[day]

                member_details = []
                for user_id, entry in members.items():
                    prefs = get_prefs(user_id)
                    logger.info(f"Listing {prefs} for registered battle")
                    user_datetime = convert_utc_to_local(prefs.get('timezone', 'UTC'), f'{utc_date} {utc_time}')

                    # Apply lambda transformation
                    member_details.append(format_member_details(prefs, entry, user_datetime))

                # only display for non-empty list
                if members or "all" in options:
                    embed.add_field(name=f"Day {day[1]} Slot {time[1]} ({utc_date} {utc_time})",
                                    value=f"{', '.join(member_details) if members else 'No registrations'}",
                                    inline=False)

        await ctx.send(embed=embed)

