import json
import os
from datetime import datetime, timedelta

import discord
import pytz
from discord.ext import commands

from core.memory import get_timezone, get_alias, get_alias_by_id
from utils.commons import has_required_permissions, parse_datetime
from utils.logger import init_logger

QUEUE_FILE = "data/queue_data.json"
QUEUES = {
    'tribune': "🎖️Tribune (Healing)",
    'elder': "🎖️Chief Elder (Gathering)",
    'priest': "🎖️Chief Priest (Building)",
    'sage': "🎖️Court Sage (Research)",
    'master': "🎖️Tactical Master (Training)",
    'praetorian': "🎖️Praetorian (PvP-Loss)",
    'border': "🎖️Border Chief (Tribes)",
    'cavalry': "🎖️Cavalry Leader (PvP-Atk/Def)"
}
EMOJIS = {"current": "➡️", "past": "✅", "date": "🗓️"}

logger = init_logger('TitleRequestQueue')

class TitleRequestQueue(commands.Cog):
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

    def find_next_available_slot(self, queue_name):
        now = datetime.now(pytz.UTC).replace(minute=0, second=0, microsecond=0)
        for i in range(72):  # Check the next 3 days
            dt = now + timedelta(hours=i)
            if all(entry["time"] != dt.isoformat() for entry in self.queues[queue_name]["entries"]):
                return dt
        return None

    @commands.command(name="queue", aliases=['q', 'q.add'])
    async def queue_add(self, ctx, queue_name: str, start_date:str = None, start_time: str = None):
        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue. Choose from {', '.join(QUEUES.keys())}.")
            return

        user_tz = get_timezone(ctx)
        now = datetime.now(pytz.timezone(user_tz))

        dt = None
        if not start_date and not start_time:
            dt = self.find_next_available_slot(queue_name)
            if not dt:
                await ctx.send("No available slots in the next 3 days.")
                return
        else:
            if not start_date:
                start_date = f'{now.year}-{now.month}-{now.day}'
            if not start_time:
                start_time = f'{now.hour}:00:00'
            dt = parse_datetime(f'{start_date} {start_time}', now)
            if not dt:
                await ctx.send("Invalid start time format. Provide at least the starting time.")
                return

        user_id = str(ctx.author.id)
        entries = self.queues[queue_name]["entries"]
        if any(e["user_id"] == user_id and abs(dt - datetime.fromisoformat(e["time"])) < timedelta(days=1) for e in
               entries):
            await ctx.send("You can only register once per queue every 24 hours.")
            return

        if dt > datetime.now(pytz.UTC) + timedelta(days=3):
            await ctx.send("You can only register up to 3 days in advance.")
            return

        entries.append({"user_id": user_id, "time": dt.isoformat()})
        entries.sort(key=lambda e: e["time"])
        self.save_queues()
        await ctx.send(f"Added {get_alias(ctx)} to {QUEUES[queue_name]} queue at {dt.strftime('%Y-%m-%d %H:%M UTC')}.")

    @commands.command(name="queue.remove", aliases=['queue.rm', 'q.rm', 'q.remove'])
    async def queue_remove(self, ctx, queue_name: str, start_time: str = None):
        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue. Choose from {', '.join(QUEUES.keys())}.")
            return

        user_id = str(ctx.author.id)
        entries = self.queues[queue_name]["entries"]

        if start_time:
            try:
                dt = (datetime.strptime(start_time, "%H")
                      .replace(minute=0, second=0, microsecond=0)
                      .astimezone(pytz.UTC))
                entry_to_remove = next((e for e in entries
                                        if e["user_id"] == user_id and
                                           datetime.fromisoformat(e["time"]).hour == dt.hour), None)
            except ValueError:
                await ctx.send("Invalid start time format. Provide at the starting hour.")
                return
        else:
            entry_to_remove = next((e for e in entries if e["user_id"] == user_id), None)

        if entry_to_remove:
            entries.remove(entry_to_remove)
            self.save_queues()
            await ctx.send(f"Removed {get_alias(ctx)} from {QUEUES[queue_name]} queue.")
        else:
            await ctx.send("No matching entry found to remove.")

    @has_required_permissions()
    @commands.command(name="q.next", aliases=['queue.next'])
    async def q_next(self, ctx, queue_name: str):
        if queue_name not in QUEUES:
            await ctx.send(f"Invalid queue.")
            return

        queue = self.queues[queue_name]
        if queue["cursor"] < len(queue["entries"]):
            queue["cursor"] += 1
            self.save_queues()
            await ctx.send(f"Advanced {queue_name} queue.")
        else:
            await ctx.send("No more entries to advance.")

    @has_required_permissions()
    @commands.command(name="q.back")
    async def q_back(self, ctx, queue_name: str):
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
    async def queue_list(self, ctx, *queue_names):
        queue_names = queue_names or QUEUES.keys()
        embed = discord.Embed(title="👑️ Imperial Title Requests 👑️", color=discord.Color.dark_gold())
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

                emoji = EMOJIS["past"] if i < queue["cursor"] else (EMOJIS["current"] if i == queue["cursor"] else "")
                user_alias = get_alias_by_id(entry['user_id'], ctx.author.name)
                user_tz =  pytz.timezone(get_timezone(ctx))
                dt = datetime.fromisoformat(entry["time"])

                description = (f"{dt.strftime('%m-%d %H:%M')} UTC\n"
                               f"{dt.astimezone(user_tz).strftime('%m-%d %H:%M')} {user_tz}")

                embed.add_field(name=f'{emoji} {user_alias}', value=description, inline=False)

            # add spacing between queues
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="", value="", inline=False)

        if not embed.fields:
            embed.description = "No entries in the queues."

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TitleRequestQueue(bot))
