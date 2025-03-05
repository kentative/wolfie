import pytest
import pytest_asyncio
from sqlalchemy import false

from cogs.wonder_battle import WonderBattle
from core.ganglia import Memory


@pytest.mark.asyncio
class TestWonderBattle:

    @pytest_asyncio.fixture
    async def battle(self, bot):
        return WonderBattle(bot)

    @pytest.mark.asyncio
    async def test_basic_flow(self, battle, ctx_user1, ctx_user2):

        await battle.cortex.forget(Memory.WONDER_BATTLE)

        await battle.add(battle, ctx_user1, "d1", "t2")
        await battle.add(battle, ctx_user2, "d2", "t1")
        await battle.add(battle, ctx_user2, "d2", "t2")

        battle_records = await battle.cortex.get_memory(Memory.WONDER_BATTLE)
        assert battle_records['d1']['t2'] == {'1': {'context': {'primary': False}}}
        assert battle_records['d2']['t1'] == {'2': {'context': {'primary': False}}}
        assert battle_records['d2']['t2'] == {'2': {'context': {'primary': False}}}

        await battle.add(battle, ctx_user1, "d1", "t2", "-p")
        battle_records = await battle.cortex.get_memory(Memory.WONDER_BATTLE)
        assert battle_records['d1']['t2'] == {'1': {'context': {'primary': True}}}

    @pytest.mark.asyncio
    async def test_advanced_flow(self, battle, ctx_user1, ctx_user2, ctx_user3):

        await battle.cortex.forget(Memory.WONDER_BATTLE)

        await battle.add(battle, ctx_user1, "d1", "t1")
        await battle.add(battle, ctx_user2, "d1", "t1")
        await battle.add(battle, ctx_user3, "d1", "t1", "-p")

        await battle.add(battle, ctx_user1, "d1", "t1", "-p")
        await battle.add(battle, ctx_user2, "d1", "t3", "-s")
        await battle.add(battle, ctx_user3, "d1", "t2", "-p")

        battle_records = await battle.cortex.get_memory(Memory.WONDER_BATTLE)
        assert battle_records['d1']['t1']['1'] ==  {'context': {'primary': True}}
        assert battle_records['d1']['t1']['2'] == {'context': {'primary': False}}
        assert battle_records['d1']['t1']['3'] == {'context': {'primary': False}}

        assert battle_records['d1']['t2']['3'] == {'context': {'primary': True}}
        assert battle_records['d1']['t3']['2'] == {'context': {'primary': False}}


    @pytest.mark.asyncio
    async def test_list(self, battle, ctx_user1, ctx_user3):

        await battle.cortex.forget(Memory.WONDER_BATTLE)

        # Register all slots for user 1
        for d in ["d1", "d2"]:
            for t in ['t1', 't2', 't3']:
                await battle.add(battle, ctx_user1, d, t)

        # list user preferences
        await battle.wonder_list(battle, ctx_user1)

        # Assert on embed properties
        embed = ctx_user1.send.call_args.kwargs.get('embed')
        assert len(embed.fields) == 6

    @pytest.mark.asyncio
    async def test_basic_all(self, battle, ctx_user1, ctx_user2):

        await battle.cortex.forget(Memory.WONDER_BATTLE)

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