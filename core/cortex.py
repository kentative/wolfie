import asyncio

from core.ganglia import Ganglia, GangliaInterface
from utils.logger import init_logger

logger = init_logger('Cortex')


class Cortex(GangliaInterface):
    def __init__(self):

        ganglia = Ganglia()

        super().__init__(ganglia)
        self._lock = asyncio.Lock()

    async def remember(self):
        async with self._lock:
            logger.info("Remembering preferences")
            await self._ganglia.save_prefs()

        return
