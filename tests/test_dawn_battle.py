import pytest
import pytest_asyncio

from cogs.dawn_battle import DawnBattle


@pytest.mark.asyncio
class TestTitleQueueE2E:

    @pytest_asyncio.fixture
    async def battle(self, bot):
        return DawnBattle(bot)

    @pytest.mark.asyncio
    async def test_basic_flow(self, battle, ctx_user1, ctx_user2):

        # Register for d1 t1 as shadow
        await battle.dawn_add.__call__(battle, ctx_user1, "d1" ,"t1", "shadow")
        await battle.dawn_add.__call__(battle, ctx_user2, "d1", "t1", "sage")
        await battle.dawn_add.__call__(battle, ctx_user2, "d1", "t2", "sage")
        await battle.dawn_add.__call__(battle, ctx_user1, "d1", "t1", "ranger")

        # Remove user2 from d1 t2
        await battle.dawn_remove.__call__(battle, ctx_user2, "d1", "t2")
        await battle.dawn_remove.__call__(battle, ctx_user2, "d1", "t2")

