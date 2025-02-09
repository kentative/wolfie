import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import discord
import pytz
from discord.ext import commands

from utils.logger import init_logger

WOLFIE_ADMIN_ROLE = os.getenv('WOLFIE_ADMIN_ROLE', 'leadership')
ALLOWED_ROLES = [ WOLFIE_ADMIN_ROLE.lower() ]

logger = init_logger('QueueManager')


def has_required_permissions():
    async def predicate(ctx):
        # Allow if user has 'manage_guild' permission
        if ctx.author.guild_permissions.manage_guild:
            return True

        # Allow if user has any of the specified roles (case-insensitive)
        if any(str(role.name).lower() in ALLOWED_ROLES for role in ctx.author.roles):
            return True

        return False

    return commands.check(predicate)

class QueueManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {
            'tribune': [],
            'elder': [],
            'priest': [],
            'sage': [],
            'master': [],
            'praetorian': []
        }
        # Initialize processed queues
        self.processed_queues = {
            'tribune_processed': [],
            'elder_processed': [],
            'priest_processed': [],
            'sage_processed': [],
            'master_processed': [],
            'praetorian_processed': []
        }
        self.queue_start_time: Optional[datetime] = None
        self.user_positions: Dict[int, str] = {
        }  # Maps user ID to their current queue position
        self.pending_leave_confirms: Dict[int, str] = {
        }  # Maps user ID to queue they're trying to leave

    def _get_next_time_slot(self, queue_name: str) -> datetime:
        """Calculate the next available time slot for a queue"""
        if not self.queue_start_time:
            # Default to current day 00:00:00 UTC if not set
            self.queue_start_time = datetime.now(pytz.UTC).replace(
                hour=0, minute=0, second=0, microsecond=0)

        queue_length = len(self.queues[queue_name])
        return self.queue_start_time + timedelta(hours=queue_length)

    @commands.command(name='q-next')
    @has_required_permissions()
    async def advance_queue(self, ctx):
        """Advance all queues to the next time slot"""
        if not self.queue_start_time:
            await ctx.send(
                "Queue start time not set. Use !q-set-time to set the start time."
            )
            return

        moved_count = 0
        for queue_name in self.queues:
            if self.queues[queue_name]:
                # Move user to processed queue
                user = self.queues[queue_name][0]
                processed_queue_name = f"{queue_name}_processed"
                self.processed_queues[processed_queue_name].append(user)

                # Remove user from original queue and positions
                if user[0] in self.user_positions:
                    del self.user_positions[user[0]]
                self.queues[queue_name] = self.queues[queue_name][1:]
                moved_count += 1

        # Advance start time by 1 hour
        self.queue_start_time += timedelta(hours=1)

        if moved_count > 0:
            await ctx.send(
                f"Advanced all queues to the next time slot. {moved_count} users were moved to processed queues."
            )
            logger.info(
                f"Queues advanced by {ctx.author.name}, {moved_count} users moved"
            )
        else:
            await ctx.send(
                "Advanced all queues to the next time slot. No users were affected."
            )
            logger.info(
                f"Queues advanced by {ctx.author.name}, no users affected")

    @commands.command(name='q-back')
    @has_required_permissions()
    async def rollback_queue(self, ctx):
        """Rollback all queues to the previous time slot"""
        if not self.queue_start_time:
            await ctx.send(
                "Queue start time not set. Use !q-set-time to set the start time."
            )
            return

        # Calculate previous time
        previous_time = self.queue_start_time - timedelta(hours=1)

        # Check if rollback would go before start time
        current_time = datetime.now(pytz.UTC)
        if previous_time < current_time.replace(hour=0,
                                                minute=0,
                                                second=0,
                                                microsecond=0):
            await ctx.send(
                "Cannot rollback beyond the starting time of the current day.")
            return

        restored_count = 0
        for queue_name in self.queues:
            processed_queue_name = f"{queue_name}_processed"
            if self.processed_queues[processed_queue_name]:
                # Get the last processed user
                user_to_restore = self.processed_queues[
                    processed_queue_name].pop()
                # Add back to front of original queue
                self.queues[queue_name].insert(0, user_to_restore)
                # Restore user position
                self.user_positions[user_to_restore[0]] = queue_name
                restored_count += 1

        # Roll back start time
        self.queue_start_time = previous_time

        if restored_count > 0:
            await ctx.send(
                f"Rolled back all queues to the previous time slot. {restored_count} users were restored."
            )
            logger.info(
                f"Queues rolled back by {ctx.author.name}, {restored_count} users restored"
            )
        else:
            await ctx.send(
                "Rolled back all queues to the previous time slot. No users were affected."
            )
            logger.info(
                f"Queues rolled back by {ctx.author.name}, no users affected")

    @commands.command(name='q-set-time', aliases=['q-set'])
    @has_required_permissions()
    async def set_queue_time(self, ctx, *, time_str: Optional[str] = None):
        """Set the starting time for all queues"""
        try:
            now = datetime.now(pytz.UTC)
            new_time: datetime
            hour: int = 0
            year: int = now.year
            month: int = now.month
            day: int = now.day

            if not time_str:
                # Default to current day 00:00:00 UTC
                new_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif '/' in time_str:
                # Parse date with optional time
                parts = time_str.split()
                date_parts = parts[0].split('/')

                if len(date_parts) == 2:  # Format: MM/DD
                    month, day = map(int, date_parts)
                elif len(date_parts) == 3:  # Format: MM/DD/YYYY
                    month, day, year = map(int, date_parts)

                if len(parts) > 1:  # Time provided
                    hour = int(parts[1])

                new_time = datetime(year, month, day, hour, 0, 0, tzinfo=pytz.UTC)
            else:
                # Just hour provided
                hour = int(time_str)
                new_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

            self.queue_start_time = new_time
            await ctx.send(f"Queue start time set to: {new_time.strftime('%Y-%m-%d %H')} UTC")
            logger.info(f"Queue start time set to {new_time} by {ctx.author}")
        except ValueError as e:
            await ctx.send("Invalid time format. Use 'MM/DD/YYYY HH', 'MM/DD HH', or just 'HH'")
            logger.error(f"Error setting queue time: {str(e)}")

    @commands.command(name='q-help')
    async def queue_help(self, ctx):
        """Display help for queue-related commands"""
        embed = discord.Embed(title="Queue Management Commands",
                              color=discord.Color.blue())

        commands_help = {
            "q-set-time":
            "Set queue start time. Examples:\n`!q-set-time 1/15/2025 8` - Jan 15, 2025 08:00 UTC\n`!q-set-time 8` - Today 08:00 UTC\n`!q-set-time 4/30` - Apr 30 00:00 UTC (admin only)",
            "q-next": "Advance queues to next time slot (admin only)",
            "q-back": "Rollback queues to previous time slot (admin only)",
            "q-tribune": "Join/leave Tribune queue",
            "q-elder": "Join/leave Chief Elder queue",
            "q-priest": "Join/leave Chief Priest queue",
            "q-sage": "Join/leave Court Sage queue",
            "q-master": "Join/leave Tactical Master queue",
            "q-praetorian": "Join/leave Praetorian Prefecture queue",
            "q-ls": "List all queues and their status"
        }

        for cmd, desc in commands_help.items():
            embed.add_field(name=f"!{cmd}", value=desc, inline=False)

        await ctx.send(embed=embed)

    async def _add_to_queue(self, ctx, position: str):
        """Helper method to add a user to a queue"""
        user_id = ctx.author.id

        # Check if user is already in this specific queue
        if user_id in self.user_positions and self.user_positions[
                user_id] == position:
            # User is trying to queue into the same queue they're already in
            if user_id in self.pending_leave_confirms:
                # User confirmed leaving
                queue_entry = next((entry for entry in self.queues[position]
                                     if entry[0] == user_id), None)
                if queue_entry:
                    self.queues[position].remove(queue_entry)
                del self.user_positions[user_id]
                del self.pending_leave_confirms[user_id]
                await ctx.send(
                    f"You have been removed from the {position} queue.")
                logger.info(f"Removed {ctx.author.name} from {position} queue")
            else:
                # Ask for confirmation
                self.pending_leave_confirms[user_id] = position
                await ctx.send(
                    f"You are already in the {position} queue. Use the same command again to leave the queue."
                )
            return

        # Check if user is in a different queue
        if user_id in self.user_positions:
            await ctx.send(
                f"You are already in the {self.user_positions[user_id]} queue. Leave that queue first."
            )
            return

        next_slot = self._get_next_time_slot(position)
        queue_entry = (ctx.author.id, ctx.author.name, next_slot)
        self.queues[position].append(queue_entry)
        self.user_positions[user_id] = position

        await ctx.send(
            f"Added {ctx.author.name} to the {position} queue for time slot: "
            f"{next_slot.strftime('%Y-%m-%d %H')} UTC")
        logger.info(f"Added {ctx.author.name} to {position} queue")

    @commands.command(name='q-tribune')
    async def queue_tribune(self, ctx):
        """Add user to Tribune queue"""
        await self._add_to_queue(ctx, 'tribune')

    @commands.command(name='q-elder')
    async def queue_elder(self, ctx):
        """Add user to Chief Elder queue"""
        await self._add_to_queue(ctx, 'elder')

    @commands.command(name='q-priest')
    async def queue_priest(self, ctx):
        """Add user to Chief Priest queue"""
        await self._add_to_queue(ctx, 'priest')

    @commands.command(name='q-sage')
    async def queue_sage(self, ctx):
        """Add user to Court Sage queue"""
        await self._add_to_queue(ctx, 'sage')

    @commands.command(name='q-master')
    async def queue_master(self, ctx):
        """Add user to Tactical Master queue"""
        await self._add_to_queue(ctx, 'master')

    @commands.command(name='q-praetorian')
    async def queue_praetorian(self, ctx):
        """Add user to Praetorian Prefecture queue"""
        await self._add_to_queue(ctx, 'praetorian')

    @commands.command(name='q-ls', aliases=['q-list'])
    async def list_queues(self, ctx):
        """List all queues and their current status"""
        embed = discord.Embed(title="Queue Status", color=discord.Color.blue())

        for position, queue in self.queues.items():
            if not queue:
                value = "--"
            else:
                # Sort queue entries by time slot
                sorted_queue = sorted(queue, key=lambda x: x[2])
                # Format the first few entries
                entries = [
                    f"{i+1}. {name} - {time.strftime('%Y-%m-%d %H')} UTC"
                    for i, (_, name, time) in enumerate(sorted_queue[:5])
                ]
                value = "\n".join(entries)
                if len(queue) > 5:
                    value += f"\n... and {len(queue) - 5} more"

            embed.add_field(name=f"{position.title()} Queue",
                            value=value,
                            inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QueueManager(bot))
