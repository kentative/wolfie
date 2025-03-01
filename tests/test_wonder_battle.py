import pytest
import pytest_asyncio

from cogs.dawn_battle import DawnBattle
from cogs.wonder_battle import WonderBattle


@pytest.mark.asyncio
class TestWonderBattle:

    @pytest_asyncio.fixture
    async def battle(self, bot):
        return WonderBattle(bot)

    @pytest.mark.asyncio
    async def test_basic_flow(self, battle, ctx_user1, ctx_user2):

        # Register all slots for user 1
        for d in ["d1", "d2"]:
            for t in ['t1', 't2', 't3']:
                await battle.add(battle, ctx_user1, d, t)

        # Register all slots for user 2
        for d in ["d1", "d2"]:
            for t in ['t1', 't2', 't3']:
                await battle.add(battle, ctx_user2, d, t)

        # Register all slots for user 1
        for d in ["d1", "d2"]:
            for t in ['t1', 't2', 't3']:
                await battle.remove(battle, ctx_user1, d, t)