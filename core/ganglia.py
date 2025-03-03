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
import json
import pathlib
from abc import ABC
from enum import Enum
from io import TextIOWrapper
from types import MappingProxyType

from discord.ext.commands import Context

from utils.logger import init_logger


# Memory configurations
class Memory(Enum):
    PREFERENCES = ("preferences", "data/user_preferences.json")
    TITLE_QUEUES = ("title_queues", "data/title_queue.json")
    DAWN_BATTLE = ("dawn_battle", "data/dawn_battle.json")
    WONDER_BATTLE = ("wonder_battle", "data/wonder_battle.json")

    def __init__(self, type_value: str, path: str):
        self.type = type_value
        self.path = path

logger = init_logger('Ganglia')

def write_data_to_path(data: dict, path: str) -> None:
    """ Writes the provided data to a JSON file at the specified path. """

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Data size in KB
    json_str = json.dumps(data, indent=2)
    data_size_kb = len(json_str) / 1024
    logger.debug(f'Saving {data_size_kb:.2f} KB to {path}')

    with open(path, "w", encoding="utf-8") as file:
        file: TextIOWrapper
        file.write(json_str)


def load_data_from_path(path: str) -> dict:
    """
    Loads data from a JSON file at the specified path.
    Returns an empty dict if the file doesn't exist.
    """
    try:
        with open(path, "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        logger.warn(f'{e}. Returning empty dict')
        return {}

class BasalGanglia(ABC):
    """Interface for all Ganglia class to supporting data persistence"""

    def __init__(self, data_path: str):
        self._data_path: str = data_path
        self.init_data: dict = {}
        self._data: dict = load_data_from_path(data_path)
        self.is_modified: bool = False

    def initialize(self, init_data: dict):
        """Initialize the Ganglia instance"""

        self.init_data = init_data
        if not self._data:
            self._data = init_data
            self.is_modified = True

    async def get(self, key: str, **kwargs):
        """Retrieve a specific entry from memory given the context"""
        return self._data.get(str(key), {})

    async def get_all(self):
        """
        Returns a read-only copy of all memory.
        Uses MappingProxyType for a true read-only view of the dictionary.
        """
        return dict(MappingProxyType(self._data))

    async def update(self, key: str, value: dict):
        """Update data entry"""
        self._data[str(key)] = value
        await self.save()

    async def save(self):
        """Save data to persistent storage"""
        write_data_to_path(self._data, self._data_path)

    async def reload(self, path: str):
        """Reload data from persistent storage"""
        self._data: dict = load_data_from_path(self._data_path)

    async def forget(self):
        """Reset to init data"""
        self._data = self.init_data


class PreferencesGanglia(BasalGanglia):
    def __init__(self):
        super().__init__(Memory.PREFERENCES.path)

    async def get(self, key: str, **kwargs):
        prefs = self._data.get(key, {})
        if not prefs and'ctx' in kwargs:
            logger.debug(f'create_default_preferences')
            ctx = kwargs['ctx']
            return await self.create_default_prefs(ctx)
        return prefs

    async def create_default_prefs(self, ctx):
        prefs = {
            'name': ctx.author.display_name,
            'alias': ctx.author.display_name,
            'timezone': 'UTC'
        }
        self._data[str(ctx.author.id)] = prefs
        logger.debug(f'created default preferences for {ctx.author.id} = {prefs}')
        await self.save()
        return prefs

class QueueGanglia(BasalGanglia):
    def __init__(self):
        super().__init__(Memory.TITLE_QUEUES.path)

class WonderBattleGanglia(BasalGanglia):
    def __init__(self):
        super().__init__(Memory.WONDER_BATTLE.path)

class DawnBattleGanglia(BasalGanglia):
    def __init__(self):
        super().__init__(Memory.DAWN_BATTLE.path)

class GangliaInterface:
    def __init__(self):
        self._lock = asyncio.Lock()

        self._memory = {
            Memory.PREFERENCES.type: PreferencesGanglia(),
            Memory.TITLE_QUEUES.type: QueueGanglia(),
            Memory.WONDER_BATTLE.type: WonderBattleGanglia(),
            Memory.DAWN_BATTLE.type: DawnBattleGanglia()
        }

    async def get_preferences(self, ctx: Context):
        return await self.get_memory(Memory.PREFERENCES, str(ctx.author.id), ctx=ctx)

    async def get_all_preferences(self):
        return await self.get_memory(Memory.PREFERENCES)

    def initialize_memory(self, mem: Memory, init_data: dict):
        self._memory[mem.type].initialize(init_data)

    async def get_memory(self, mem: Memory, key: str = None, **kwargs):
        return await self._execute(mem, 'get', key, **kwargs) if key \
            else await self._execute(mem, 'get_all')

    async def update_memory(self, mem: Memory, key: str, value :dict) -> dict:
        await self._execute(mem, 'update', key, value)
        self._memory[mem.type].is_modified = True

    async def save_memory(self, mem: Memory):
        return await self._execute(mem, 'save')

    async def _execute(self, mem: Memory, operation: str, *args, **kwargs):
        async with self._lock:
            storage = self._memory[mem.type]
            method = getattr(storage, operation)
            logger.info(f"{operation} {mem.type} with args: {args}")
            return await method(*args, **kwargs)
