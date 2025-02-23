from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from freezegun import freeze_time

from tests.test_title_queue import validate_entries, count_queue_size

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

        self._clear(title_queue)

        # Add 3 entries every hour
        await title_queue.queue_add.__call__(title_queue, ctx_user1, "sage", *create_datetime(0))
        await title_queue.queue_add.__call__(title_queue, ctx_user2, "sage", *create_datetime(1))
        await title_queue.queue_add.__call__(title_queue, ctx_user3, "sage", *create_datetime(2))
        assert 3, count_queue_size(title_queue.queues)
        validate_entries(title_queue.queues)

        # remove 2nd entry (user2)
        await title_queue.queue_remove.__call__(title_queue, ctx_user2, "sage", None)
        assert 2, count_queue_size(title_queue.queues)
        validate_entries(title_queue.queues)

        # add user1 entry (02-22)
        await title_queue.queue_add.__call__(title_queue, ctx_user1, "sage", *create_datetime(0, 1))
        assert 3, count_queue_size(title_queue.queues)
        validate_entries(title_queue.queues)

        # remove user1 first entry (02-21)
        await title_queue.queue_remove.__call__(title_queue, ctx_user1, "sage", "2-21")
        assert 2, count_queue_size(title_queue.queues)
        validate_entries(title_queue.queues)


    @staticmethod
    def _clear(title_queue):
        title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

def create_datetime(hours: int, days: int = 0):
    now = datetime.now()
    now += timedelta(days=days, hours=hours)
    date = now.strftime("%m-%d")
    time = now.strftime("%H:%M")
    return date, time