from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from dateutil import parser
from dotenv import load_dotenv
from freezegun import freeze_time

from tests.test_title_queue import validate_entries

load_dotenv()

from cogs.title_queue import TitleQueue

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

FIXED_TIME = "2025-02-21 21:00:00"
NUM_USERS = 3


@pytest.mark.asyncio
class TestTitleQueueE2E:

    @pytest_asyncio.fixture
    async def title_queue(self, bot):
        return TitleQueue(bot)

    @pytest.mark.asyncio
    @freeze_time(FIXED_TIME)
    async def test_basic_flow(self, title_queue, ctx_user1, ctx_user2, ctx_user3):

        date = "2-21"
        time = datetime.now()
        time += timedelta(hours=1)


        self._clear(title_queue)
        await title_queue.queue_add.__call__(title_queue, ctx_user1, "sage", date, time.strftime("%H:%M"))

        time += timedelta(hours=1)
        await title_queue.queue_add.__call__(title_queue, ctx_user2, "sage", date, time.strftime("%H:%M"))

        validate_entries(title_queue.queues, "per_hour")

    @staticmethod
    def _clear(title_queue):
        title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}