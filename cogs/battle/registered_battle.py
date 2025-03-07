from datetime import datetime, timedelta

import discord
import pytz
from discord.ext import commands

from core.ganglia import Memory
from utils.logger import init_logger
from utils.prefs_utils import get_timezone, get_alias

DATE_DISPLAY_FORMAT = '%m-%d %H:%M %Z'
TIME_MAPPING = {"t1": "01:00 UTC", "t2": "11:00 UTC", "t3": "19:00 UTC"}
TIME_ICON = {"t1": "🕐", "t2": "🕚", "t3": "🕖"}
PRIMARY_ICON = {"primary": "⚔️️", "secondary": ""}

logger = init_logger('RegisteredBattle')

def get_weekend_dates(user_tz):
    """Returns the dates for the upcoming Saturday (d1) and Sunday (d2) in the user's local timezone."""
    today = datetime.now(pytz.UTC)
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
        "%Y-%m-%d %H:%M UTC").replace(tzinfo=pytz.UTC)

    return utc_dt.astimezone(user_timezone)

def convert_timeslot_to_utc(day_slot: str, time_slot: str) -> str:
    """Returns "%m-%d %H:%M UTC" from a d1, t1 and timezone"""
    d1_date, d2_date = get_weekend_dates('UTC')
    date_mapping = {"d1": d1_date, "d2": d2_date}
    return f'{date_mapping.get(day_slot)} {TIME_MAPPING.get(time_slot)}'


async def parse_slot_option(ctx, options):
    try:
        # Initialize return values as None
        filtered_day = None
        filtered_time = None

        option_parts = options[1:].lower()  # Remove the leading -

        # Handle day-only format (-d#)
        if option_parts.startswith('d') and len(option_parts) == 2:
            day_num = int(option_parts[1])
            if day_num in [1, 2]:
                filtered_day = f"d{day_num}"
            else:
                await ctx.send("Invalid day number. Use 1 or 2.")
                return

        # Handle time-only format (-t#)
        elif option_parts.startswith('t') and len(option_parts) == 2:
            time_num = int(option_parts[1])
            if time_num in [1, 2, 3]:
                filtered_time = str(time_num)
            else:
                await ctx.send("Invalid time slot number.")
                return

        # Handle combined format (-d#t#)
        elif len(option_parts) == 4 and option_parts[0] == 'd' and option_parts[2] == 't':
            day_num = int(option_parts[1])
            time_num = int(option_parts[3])

            # Validate day number
            if day_num in [1, 2]:
                filtered_day = f"d{day_num}"
            else:
                await ctx.send("Invalid day number. Use 1 or 2.")
                return

            # Validate time slot
            if time_num in [1, 2, 3]:
                filtered_time = str(time_num)
            else:
                await ctx.send("Invalid time slot number.")
                return

        else:
            await ctx.send("Invalid format. Use -d# or -t# or -d#t# (e.g., -d1, -t2, or -d1t2)")
            return

    except (IndexError, ValueError):
        await ctx.send("Invalid format. Use -d# or -t# or -d#t# (e.g., -d1, -t2, or -d1t2)")
        return

    logger.info(f"Filtering for {filtered_day} {filtered_time}")
    return filtered_day, filtered_time


class RegisteredBattle(commands.Cog):
    def __init__(self, title: str, memory: Memory, bot):
        self.battle_title = title
        self.memory = memory
        self.cortex = bot.cortex
        self.max_team_size = 30
        self.cortex.initialize_memory(
            memory, {
                # Dictionary to store team registrations
                "d1": {"t1": {}, "t2": {}, "t3": {}},
                "d2": {"t1": {}, "t2": {}, "t3": {}}
            })

    async def register(self, ctx,
                       day: str = commands.parameter(description="use d1 or d2"),
                       time: str = commands.parameter(description="use t1, t2 or t3"),
                       **context):
        """Register user for a specific day and time slot."""
        day = day.lower()
        time = 't' + time[1:].lower()  # allow slot and time


        day_slots = await self.cortex.get_memory(self.memory)
        if day not in day_slots or time not in day_slots[day]:
            await ctx.send("Invalid day or time slot. Use d1/d2 and t1/t2/t3.")
            return

        time_slot: dict = day_slots[day][time]
        user_id = str(ctx.author.id)  # Ensure user_id is stored as a string for JSON compatibility

        # If registering as primary, remove primary flag from all other slots
        if context.get('primary', False):
            for d in day_slots:
                for t in day_slots[d]:
                    if user_id in day_slots[d][t] and day_slots[d][t][user_id]['context'].get('primary', False):
                        if d == day and t == time:
                            continue  # Skip current slot
                        # Remove primary flag from other slot
                        day_slots[d][t][user_id]['context']['primary'] = False
                        await ctx.send(f"Removed primary {d} {t} slot")

        if user_id in time_slot:
            await ctx.send("Updating your entry for this slot!")
            time_slot[user_id]["context"].update(context)  # Update existing entry instead of overwriting

        else:
            if len(time_slot) >= self.max_team_size:
                await ctx.send(f"This time slot is full ({self.max_team_size} players max). Try another slot.")
                return

            # Create new entry
            time_slot[user_id] = {"context": context}

        await self.cortex.remember(self.memory)

        # User data
        user_prefs = await self.cortex.get_preferences(ctx)
        user_tz = get_timezone(user_prefs)
        user_alias = get_alias(user_prefs)

        utc_datetime = convert_timeslot_to_utc(day, time)
        local_time = convert_utc_to_local(user_tz, utc_datetime)
        await ctx.send(f"{user_alias} has been registered for {local_time.strftime(DATE_DISPLAY_FORMAT)}")

    async def unregister(self, ctx,
                     day: str = commands.parameter(description="use d1 or d2"),
                     time: str = commands.parameter(description="use t1, t2 or t3")):
        """Remove user from a specific day and time slot."""
        day = day.lower()
        time = 't' + time[1:].lower()  # allow slot and time

        teams = await self.cortex.get_memory(self.memory)
        if day not in teams or time not in teams[day]:
            await ctx.send("Invalid day or time slot. Use d1/d2 and t1/t2/t3.")
            return

        team: dict = teams[day][time]
        user_id = str(ctx.author.id)

        # User data
        user_prefs = await self.cortex.get_preferences(ctx)
        user_alias = get_alias(user_prefs)

        if user_id in team:
            del team[user_id]  # Remove the user from the time slot
            await self.cortex.remember(self.memory)
            logger.info("Successfully removed.")
            await ctx.send(f"{user_alias} has been removed from {day.upper()} {time.upper()}.")
        else:
            logger.warn("Not registered for this time slot.")
            await ctx.send("You are not registered for this time slot.")


    @staticmethod
    def format_member(prefs: dict, entry: dict, user_datetime: datetime):
        return f'{prefs.get("alias", "Unknown")} ({user_datetime.strftime(DATE_DISPLAY_FORMAT)})'


    async def list_registration(self, ctx,
                                options: str = commands.parameter(
                                    description="a 'all slots', d#t# 'day and time slot'",
                                    default="non-empty"),
                                format_member_details: callable = format_member):

        """List current registration information in UTC."""
        d1_date, d2_date = get_weekend_dates('UTC')
        day_mapping = {"d1": d1_date, "d2": d2_date}

        all_prefs = await self.cortex.get_all_preferences()
        embed = discord.Embed(title=self.battle_title, color=discord.Color.dark_gold())
        teams = await self.cortex.get_memory(self.memory)

        # Parse -d#t# option
        filtered_day = None
        filtered_time = None
        if isinstance(options, str) and options.startswith("d"):
            filtered_day, filtered_time = await parse_slot_option(ctx, options)

        for day, slots in teams.items():
            # Skip if filtered_day is set and doesn't match current day
            if filtered_day and day != filtered_day:
                continue

            for time, members in slots.items():
                # Skip if filtered_time is set and doesn't match current time
                if filtered_time and time != filtered_time:
                    continue

                logger.info(f"Listing entries for {day} {slots}")
                utc_time = TIME_MAPPING[time]
                utc_date = day_mapping[day]

                member_details = []
                for user_id, entry in members.items():
                    prefs = all_prefs.get(user_id, {})
                    logger.info(f"Listing {prefs} for registered battle")
                    user_datetime = convert_utc_to_local(prefs.get('timezone', 'UTC'), f'{utc_date} {utc_time}')

                    # Apply lambda transformation
                    member_details.append(format_member_details(prefs, entry, user_datetime) + "\n")

                # only display for non-empty list
                if members or "all" in options or "a" in options:
                    embed.add_field(name=f"🗓️ Day {day[1]} Slot {time[1]} ({utc_date} {utc_time})",
                                    value=f"{''.join(member_details) if members else 'No registrations'}",
                                    inline=False)

        await ctx.send(embed=embed)
