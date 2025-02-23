import json
import os
from datetime import datetime, timedelta

import discord
import pytz
from dateutil import parser
from discord.ext import commands

from core.memory import get_alias, get_alias_by_id, get_timezone_by_id, get_prefs
from tests.conftest import MockContext
from utils.commons import has_required_permissions, parse_datetime, parse_date_input, parse_time_input, \
    read_iso_datetime
from utils.logger import init_logger

QUEUE_FILE = "data/queue_data.json"
QUEUES = {
    'tribune': "🏆 Tribune (Healing) 🏆",
    'elder': "🏆 Elder (Gathering) 🏆",
    'priest': "🏆 Priest (Building) 🏆",
    'sage': "🏆 Sage (Research) 🏆",
    'master': "🏆 Master (Training) 🏆",
    'praetorian': "🏆 Praetorian (PvP-Loss) 🏆",
    'border': "🏆 Border (Tribes) 🏆",
    'cavalry': "🏆 Cavalry (PvP-Atk/Def) 🏆"
}
EMOJIS = {"current": "⏳", "past": "✅", "date": "🗓️", "left": "⬅️", "waiting": "⏳"}

logger = init_logger('TitleQueue')

class TitleQueue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}
        self.load_queues()

    def load_queues(self):
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r") as f:
                self.queues.update(json.load(f))

    def save_queues(self):
        with open(QUEUE_FILE, "w") as f:
            json.dump(self.queues, f, indent=4)

    def find_next_available_slot(self, queue_name:str, user_tz:str):
        """ find the next time slot based on current entry in the queue"""

        # get current entry
        queue = self.queues[queue_name]
        queue_entries = queue['entries']
        cursor = queue['cursor']
        logger.info(f"queue_entries: {json.dumps(queue_entries, indent=2)}, cursor: {cursor}")

        current_entry = queue_entries[cursor] \
            if len(queue_entries) > 0 and cursor < len(queue_entries) else None
        now = datetime.now(pytz.timezone(user_tz))
        if now.minute > 30:
            now = now + timedelta(hours=1)
            logger.info(f"rounding to the next hour {now}")
        now = now.replace(minute=0, second=0, microsecond=0)
        next_available_dt = read_iso_datetime(current_entry["time"]) if current_entry else now

        # use next_available_dt only if it's later than now
        dt = next_available_dt if next_available_dt > now else now
        for i in range(72):  # Check the next 3 days
            dt = dt + timedelta(hours=1)
            logger.info(f"next available time + {i} hour={dt} ")
            if all(read_iso_datetime(entry["time"]) != dt for entry in queue_entries):
                logger.info(f"found available time: {dt.isoformat()} ")
                return dt
        return None

    @commands.command(name="queue", aliases=['q', 'q.add'])
    async def queue_add(self, ctx,
                        queue_name: str=commands.parameter(description="- one of (tribune, elder, priest, sage, master, praetorian, border, cavalry"),
                        start_date: str=commands.parameter(description="- Optional. ex: 2025-02-14 or 2-15", default=None),
                        start_time: str = commands.parameter(description="- Optional. ex: 15 or 3PM", default=None)):
        """
        Add yourself to the queue. Specify the queue name. Defaults to the next available slot.
        - Example: !queue.add sage 2-15 3PM
        - Queue names: tribune, elder, priest, sage, master, praetorian, border, cavalry
        """

        logger.info(f"{get_prefs(ctx.author.id)}\n "
                    f"!Queue.add ctx: {ctx.author.id} ({queue_name}, {start_date}, {start_time}) "
                    f"now: {datetime.now().astimezone(pytz.UTC)}")

        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue. Choose from {', '.join(QUEUES.keys())}.")
            return

        user_id = str(ctx.author.id)
        user_tz = get_timezone_by_id(user_id)
        now = datetime.now(pytz.timezone(user_tz))
        now = now.replace(minute=0, second=0, microsecond=0)

        if not start_date and not start_time:
            dt = self.find_next_available_slot(queue_name, user_tz)
            logger.info(f"start date and time not specified, using next available slot: {dt}")
            if not dt:
                await ctx.send("No available slots in the next 3 days.")
                return
        else:
            parsed_date = parse_date_input(start_date, user_tz)

            # try parsing date as time
            if not parsed_date and not start_time:
                start_time = start_date
                parsed_time = parse_time_input(start_time, user_tz)
                parsed_date = f'{now.year}-{now.month}-{now.day}'
            else:
                parsed_time = parse_time_input(start_time, user_tz)
                if not parsed_time:
                    parsed_time = f'{now.hour}:00:00'

            logger.info(f"date input: {start_date} = {parsed_date} time input: {start_time} = {parsed_time}")
            dt = parse_datetime(f'{parsed_date} {parsed_time}', user_tz)

        logger.info(f"final parsed datetime: {dt} UTC: {dt.astimezone(pytz.UTC)}")
        if not dt:
            logger.warn(f"Invalid datetime format {start_date} {start_time}")
            await ctx.send("Invalid start time format. Use 'mm-dd hh'")
            return

        if dt < now:
            logger.warn("Time is in the past")
            await ctx.send("Invalid start time. Please specify the hour in the future.")
            return

        entries = self.queues[queue_name]["entries"]
        if any(e["user_id"] == user_id and abs(dt - datetime.fromisoformat(e["time"])) < timedelta(days=1) for e in
               entries):
            logger.warn("Only one entry per day")
            await ctx.send("You can only register once per queue every 24 hours.")
            return

        if dt > datetime.now(pytz.UTC) + timedelta(days=3):
            logger.warn("Can only queue 3 days in advanced")
            await ctx.send("You can only register up to 3 days in advance.")
            return

        logger.info(f"checking available time for: {dt}")
        for entry in entries:
            entry_time = read_iso_datetime(entry["time"])
            logger.info(f"entry time {entry_time}")
            if entry_time == dt:
                logger.warn("Slot already taken")
                await ctx.send(f"Time slot is already taken. Please select another slot.")
                return

        # queue entry
        entries.append({
            "user_id": user_id,
            "user_name": get_alias(ctx),
            "time": dt.isoformat()
         })

        entries.sort(key=lambda e: parser.isoparse(e["time"]))
        self.save_queues()
        logger.info(f"Successfully added {ctx.author.id} to queue")
        await ctx.send(f"Added {get_alias(ctx)} to {QUEUES[queue_name]} queue at {dt.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')}.")

        if not isinstance(ctx, MockContext): # do not list during testing
            await self.queue_list(ctx, queue_name)


    @commands.command(name="queue.remove", aliases=['queue.rm', 'q.rm', 'q.remove'])
    async def queue_remove(self, ctx,
                           queue_name: str=commands.parameter(description="- the queue name"),
                           start_date: str=commands.parameter(description="- Optional. ex: 02-14 or 2-15", default=None)):
        """
        Remove yourself from the queue. Specify the queue name.
		- Example 1: !queue.remove master (remove entry for current day)
		- Example 2: !queue.remove master 2-23 (remove entry for that that day)
        """
        logger.info(f"{get_prefs(ctx.author.id)}\n "
                    f"!Queue.remove ctx: {ctx.author.id} ({queue_name}, {start_date}) "
                    f"now: {datetime.now().astimezone(pytz.UTC)}")

        if queue_name not in QUEUES:
            logger.info(f'invalid queue name {queue_name}')
            await ctx.send(f"Invalid queue. Choose from {', '.join(QUEUES.keys())}.")
            return

        user_id = str(ctx.author.id)
        user_tz = get_timezone_by_id(user_id)
        queue =  self.queues[queue_name]
        cursor = int(queue['cursor'])
        entries = queue["entries"]

        if start_date:
            try:
                parsed_date = parse_date_input(start_date, user_tz)
                entry_to_remove = next((e for e in entries
                    if e["user_id"] == user_id and
                       datetime.fromisoformat(e["time"]).strftime("%Y-%m-%d") == parsed_date), None)

            except ValueError:
                logger.error(f'Invalid datetime format {start_date}')
                await ctx.send("Invalid datetime format. Provide the date to remove: 'mm-dd'")
                return
        else:
            entry_to_remove = next((e for e in entries if e["user_id"] == user_id), None)

        if entry_to_remove:
            # update cursor value
            entry_index = entries.index(entry_to_remove)
            if entry_index <= cursor:
                queue['cursor'] = cursor -1

            entries.remove(entry_to_remove)
            self.save_queues()
            await ctx.send(f"Removed {get_alias(ctx)} from {QUEUES[queue_name]} queue.")

            logger.info(f"Successfully remove {ctx.author.id} from {queue_name}")
            if not isinstance(ctx, MockContext): # do not list during testing
                await self.queue_list(ctx, queue_name)
        else:
            await ctx.send("No matching entry found to remove.")

    @has_required_permissions()
    @commands.command(name="queue.next", aliases=['q.next', 'q.n'])
    async def queue_next(self, ctx,
                         queue_name: str=commands.parameter(description="- the queue name"),
                         count: int=commands.parameter(description="number of entries to advance. default 1", default=1)):
        """
        To be used by title provider. Advance the queue to the next user.
        - Example: !queue.next master
        """
        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue.")
            return

        if count < 1:
            await ctx.send(f"Count must be at least 1.")

        queue = self.queues[queue_name]
        queue_size = len(queue["entries"])
        cursor = queue["cursor"]
        if count + cursor > len(queue):
            count = queue_size - cursor
            if count != 1:
                await ctx.send(f"Count value exceeds queue size. Changing to {count}")

        logger.info(f"Advancing queue. cursor: {cursor} count: {count} size: {queue_size}")
        if queue["cursor"] < queue_size:
            queue["cursor"] += count
            self.save_queues()
            entry = queue["entries"][queue["cursor"] -1]
            await ctx.send(f"<@{entry.get('user_id')}>, your title is available!")

        else:
            await ctx.send("No more entries to advance.")

    @has_required_permissions()
    @commands.command(name="queue.back", aliases=['q.back', 'q.b'])
    async def queue_back(self, ctx, queue_name: str=commands.parameter(description="- the queue name")):
        """
        To be used by title provider. Rollback the queue to the previous user.
        - Example: !queue.back master
        """
        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue.")
            return

        queue = self.queues[queue_name]
        if queue["cursor"] > 0:
            queue["cursor"] -= 1
            self.save_queues()
            await ctx.send(f"Reverted {queue_name} queue.")
        else:
            await ctx.send("No previous entries to revert.")

    @commands.command(name="queue.list", aliases=['q.list', 'q.ls'])
    async def queue_list(self, ctx, *queue_names: str):
        """Display the queue entries. Example: !queue.list sage master ..."""

        queue_names = queue_names or QUEUES.keys()
        embed = discord.Embed(title="👑 --= IMPERIAL TITLES =-- 👑", color=discord.Color.dark_gold())
        embed.add_field(name="", value="", inline=False)

        for queue_name in queue_names:
            if queue_name.lower() not in QUEUES:
                continue

            queue = self.queues[queue_name]
            if len(queue['entries']) == 0:
                continue # skip empty queue

            # Display Queue name
            embed.add_field(name=QUEUES[queue_name], value="", inline=False)

            # Display queue entries with UTC and Local time
            for i, entry in enumerate(queue["entries"]):

                logger.info(f"{queue_name} entry: {entry}")
                entry_id = entry['user_id']
                entry_alias = get_alias_by_id(entry_id, entry.get('user_name'))

                # message details
                emoji = EMOJIS["past"] if i < queue["cursor"] \
                    else (EMOJIS["current"] if i == queue["cursor"] else EMOJIS["waiting"])

                entry_tz =  pytz.timezone(get_timezone_by_id(entry_id))
                dt = datetime.fromisoformat(entry["time"])

                description = f"{dt.astimezone(entry_tz).strftime('%m-%d %H:%M')} {entry_tz}" \
                    if entry_tz.zone != "UTC" else ""

                embed.add_field(name=f'{emoji}  {i+1}. {entry_alias} ({dt.astimezone(pytz.UTC).strftime("%m-%d %H:%M")})',
                                value=description,
                                inline=False)

            # add spacing between queues
            embed.add_field(name="", value="", inline=False)

        if not embed.fields:
            embed.description = "No entries in the queues."

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TitleQueue(bot))
