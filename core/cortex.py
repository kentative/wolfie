import asyncio

from core.ganglia import GangliaInterface, Memory
from utils.logger import init_logger

logger = init_logger('Cortex')


class Cortex(GangliaInterface):
    def __init__(self):
        super().__init__()
        self._lock = asyncio.Lock()

    async def remember(self, memory: Memory = None):
        for memory_name, memory_class in self._memory.items():
            if memory_class.is_modified or memory_name == memory.type:
                logger.info(f"remembering: {memory_name}")
                await memory_class.save()

    async def forget(self, memory: Memory):
        await self._memory[memory.type].forget()
