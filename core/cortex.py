import asyncio

from core.ganglia import GangliaInterface, Memory
from utils.logger import init_logger

logger = init_logger('Cortex')


class Cortex(GangliaInterface):
    def __init__(self):
        super().__init__()
        self._lock = asyncio.Lock()

    async def get_user_details(self, user_id):
        user_details = {}
        for memory_name, memory_class in self._memory.items():
            logger.info(f"retrieving data from: {memory_name}")
            user_details[memory_name] = await memory_class.get(user_id)
        return user_details

    async def record_event(self, key, event_details: dict):
        await self.update_memory(Memory.SHARED_EVENTS, key, event_details)
        await self.remember(Memory.SHARED_EVENTS)

    async def remember(self, memory: Memory = None):
        for memory_name, memory_class in self._memory.items():
            if memory_class.is_modified or memory_name == memory.type:
                logger.info(f"remembering: {memory_name}")
                await memory_class.save()

    async def forget(self, memory: Memory):
        await self._memory[memory.type].forget()
