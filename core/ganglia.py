"""
Ganglia Module - Core and Frequently access Memory Module

This module implements the memory for the bot,
functioning as a primary data access and persistence layer. It manages direct
access to individual cog data and handles data persistence operations.

Architecture:
    The Ganglia module serves as the lowest level of the bot's memory hierarchy,
    providing direct access to individual cog data without requiring higher-level
    processing through the Thalamus or Cortex.

Key Components:
    Ganglia:
        Core class handling direct memory access and persistence
        - Manages individual cog data storage and retrieval
        - Handles data persistence to JSON files
        - Provides atomic operations for data access

    GangliaInterface:
        Interface class providing controlled access to memory storage
        - Mediates access to preferences, queues, and battle data
        - Implements thread-safe operations through async locks

Responsibilities:
    - Direct cog data access and updates
    - Data persistence management
"""

import asyncio
from types import MappingProxyType

from discord.ext.commands import Context

from utils.datetime_utils import load_user_prefs, save_user_prefs
from utils.logger import init_logger

logger = init_logger('Ganglia')


class Ganglia:
    """The internal implementation of the memory component"""
    def __init__(self):
        self._user_prefs: dict = load_user_prefs()


    async def get_timezone(self, ctx):
        return (self._user_prefs.get(str(ctx.author.id), {})
                .get('timezone', 'UTC'))


    async def get_timezone_by_id(self, user_id: str):
        return (self._user_prefs.get(str(user_id), {})
                .get('timezone', 'UTC'))


    async def get_alias(self, ctx):
        return (self._user_prefs.get(str(ctx.author.id), {})
                .get('alias', ctx.author.name))


    async def get_alias_by_id(self, user_id: str, default: str):
        return self._user_prefs.get(str(user_id), {}).get('alias', default)


    async def get_preferences(self, ctx):
        prefs = self._user_prefs.get(str(ctx.author.id), {})
        if not prefs:
            logger.debug(f'create_default_preferences')
            return await self.create_default_preferences(ctx)
        return prefs


    async def get_preferences_by_id(self, user_id):
        return self._user_prefs.get(str(user_id), {})


    async def get_preferences_all(self) -> dict:
        """
        Returns a read-only copy of the entire user preferences dictionary.
        Uses MappingProxyType for a true read-only view of the dictionary.
        """
        return dict(MappingProxyType(self._user_prefs))


    async def create_default_preferences(self, ctx):
        prefs = {
            'name': ctx.author.display_name,
            'alias': ctx.author.display_name,
            'timezone': 'UTC'
        }
        self._user_prefs[str(ctx.author.id)] = prefs
        logger.debug(f'created default preferences for {ctx.author.id} = {prefs}')
        await self.save_prefs()
        return prefs


    async def save_prefs(self):
        save_user_prefs(self._user_prefs)


    async def update_prefs(self, user_id: str, new_prefs: dict):
        self._user_prefs[str(user_id)] = new_prefs
        await self.save_prefs()


class GangliaInterface:
    """
    Provides direct access to the memory storage
    """
    def __init__(self, ganglia: Ganglia):
        self._lock = asyncio.Lock()
        self._ganglia = ganglia

    async def get_preferences_by_id(self, user_id: str):
        async with self._lock:
            logger.info(f"getting preferences by id: {user_id}")
            return await self._ganglia.get_preferences_by_id(user_id)

    async def get_preferences(self, ctx: Context):
        async with self._lock:
            logger.info(f"getting preferences by ctx: {ctx.author.id}")
            return await self._ganglia.get_preferences(ctx)

    async def get_all_preferences(self) -> dict:
        async with self._lock:
            logger.info(f"getting all preferences")
            return await self._ganglia.get_preferences_all()

    async def update_preferences(self, ctx: Context, preferences: dict):
        async with self._lock:
            logger.info(f"updating preferences {preferences}")
            return await self._ganglia.update_prefs(str(ctx.author.id), preferences)

    async def get_all_queue_entries(self, queue_name: str = "title_queue"):
        pass

    async def get_queue_entry(self, ctx: Context):
        pass

    async def update_queue_entry(self, ctx: Context):
        pass

    async def get_battle_entry(self, ctx: Context):
        pass

    async def update_battle_entry(self, ctx: Context):
        pass