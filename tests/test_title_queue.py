import pytest
import pytest_asyncio
import pytz
from dateutil import parser
from dotenv import load_dotenv
from freezegun import freeze_time

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

NUM_USERS = 3


@pytest.mark.asyncio
class TestTitleQueue:

    @pytest_asyncio.fixture
    async def title_queue(self, bot):
        return TitleQueue(bot)

    @pytest.mark.asyncio
    async def test_single_queue(self, title_queue, ctx_user1, ctx_user2, ctx_user3):
        """Test joining a queue"""

        queue_names = QUEUES.keys()
        users = [ctx_user1, ctx_user2, ctx_user3]

        # clear the queues
        title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

        for ctx in users:
            await title_queue.queue_add.__call__(title_queue, ctx, "sage", None, None)

        total_entries = self._count_queue_size(title_queue.queues)
        assert total_entries == NUM_USERS
        validate_entries(title_queue.queues, "per_hour")

    @pytest.mark.asyncio
    async def test_queue_join(self, title_queue, ctx_user1, ctx_user2, ctx_user3):
        """Test joining a queue"""

        queue_names = QUEUES.keys()
        users = [ctx_user1, ctx_user2, ctx_user3]

        # clear the queues
        title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

        for name in queue_names:
            for ctx in users:
                await title_queue.queue_add.__call__(title_queue, ctx, name, None, None)

        total_entries = self._count_queue_size(title_queue.queues)
        assert total_entries == len(queue_names) * NUM_USERS
        validate_entries(title_queue.queues, "per_hour")

    @pytest.mark.asyncio
    async def test_queue_join_date(self, title_queue, ctx_user1, ctx_user2, ctx_user3):
        """Test joining a queue with date format"""

        with freeze_time("2025-02-21 21:00:00-08:00"):
            users = [ctx_user1, ctx_user2, ctx_user3]
            dates = [
                '2-21','2/21', '2.21', '21/2', # one unique
                '2-22', # future, OK
                '2.20'  # past, NOK
             ]

            # clear the queues
            title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

            for ctx in users:
                for date in dates:
                    await title_queue.queue_add.__call__(title_queue, ctx, "sage", date, None)

            total_entries = self._count_queue_size(title_queue.queues)
            assert total_entries == 2
            validate_entries(title_queue.queues)

    @pytest.mark.asyncio
    async def test_queue_join_time(self, title_queue, ctx_user1, ctx_user2, ctx_user3):
        """Test joining a queue with time format"""

        with freeze_time("2025-02-21 21:00:00-08:00"):
            users = [ctx_user1]
            times = [
                '21','9PM', '21:00', '21:02:01', # one unique
                '10PM', # future, < 24hr NOK
                '23',   # future, < 24hr NOK
                '9:00'  # past, NOK
             ]

            # clear the queues
            title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

            for ctx in users:
                for time in times:
                    await title_queue.queue_add.__call__(title_queue, ctx, "sage", time, None)

            total_entries = self._count_queue_size(title_queue.queues)
            assert total_entries == 1
            validate_entries(title_queue.queues)

    @pytest.mark.asyncio
    @freeze_time("2025-02-21 21:00:00-08:00")
    async def test_queue_join_datetime(self, title_queue, ctx_user1, ctx_user2, ctx_user3):
        """Test joining a queue with a date and time format"""

        users = [ctx_user1]
        dates = [
            '2-20', # past        NOK
            '2-21', # present     OK
            '2.22', # future      OK
            '2.24', # future      OK
            '2.25'  # too far     NOK
         ]
        times = [   #            | 20  | 21     | 22     |  24     |
            '8PM',  # past       | NOK |NOK-Past| NOK<24 |  OK     |
            '11PM', # future     | NOK | NOK<24 | NOK<24 | NOK <24 |
            '10PM'  # current    | NOK | OK     | OK     | NOK <24 |
         ]

        # clear the queues
        title_queue.queues = {queue: {"entries": [], "cursor": 0} for queue in QUEUES}

        for ctx in users:
            for date in dates:
                for time in times:
                    await title_queue.queue_add.__call__(title_queue, ctx, "sage", date, time)

        total_entries = self._count_queue_size(title_queue.queues)
        assert total_entries == 3
        validate_entries(title_queue.queues)

    @staticmethod
    def _count_queue_size(data):

        entries = {key: len(value["entries"]) for key, value in data.items()}
        total_count = 0
        for category, count in entries.items():
            total_count = total_count + count

        return total_count


def validate_entries(queues, options=None):
    if options is None:
        options = []
    for category, details in queues.items():
        entries = details["entries"]

        if not entries:
            continue

        seen_entries = set()  # Track unique (user_id, time) pairs
        previous_time = None
        previous_user_id = None
        for entry in entries:
            user_id = entry["user_id"]
            entry_time = parser.isoparse(entry["time"])  # Parse into datetime

            # 1a. Ensure time is unique
            if previous_time and entry_time == previous_time:
                raise Exception(f"{category}: Time entries must be unique ({entry_time})")

            # 1b. Ensure time is sorted ascending
            if previous_time and entry_time < previous_time:
                raise Exception(f"{category}: Time entries must be in ascending order"
                                f" {previous_user_id}:({previous_time.astimezone(pytz.UTC)}) "
                                f" {user_id}:({entry_time.astimezone(pytz.UTC)})"
                                f" delta: {entry_time - previous_time}")

            # 2. Check for duplicate (user_id, time)
            if (user_id, entry_time) in seen_entries:
                raise Exception(f"{category}: Duplicate entry found for user_id {user_id} at {entry_time}")

            seen_entries.add((user_id, entry_time))
            previous_time = entry_time
            previous_user_id = user_id

        # 3. Check 1-hour interval consistency
        if "per_hour" in options:
            for i in range(1, len(entries)):
                time1 = parser.isoparse(entries[i - 1]["time"]).astimezone()  # Convert to UTC
                time2 = parser.isoparse(entries[i]["time"]).astimezone()  # Convert to UTC

                delta = time2 - time1
                hours, remainder = divmod(delta.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)

                if delta.total_seconds() != 3600:
                    raise Exception(
                        f"{category}: Time entries are not exactly 1 hour apart ({time1} -> {time2}), "
                        f"actual difference: {int(hours)}h {int(minutes)}m {int(seconds)}s"
                    )