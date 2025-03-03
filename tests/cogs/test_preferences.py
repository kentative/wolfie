import pytest
import pytest_asyncio

from cogs.preferences import Preferences
from core.ganglia import Memory


@pytest.mark.asyncio
class TestPreferences:

    @pytest_asyncio.fixture
    async def preferences(self, bot):
        return Preferences(bot)

    @pytest.mark.asyncio
    async def test_basic_flow(self, preferences, ctx_user1, ctx_user2, ctx_user3):

        # clear user preferences
        await preferences.cortex.forget(Memory.PREFERENCES)

        # set user preferences
        await preferences.set_name.__call__(preferences, ctx_user1, "alias1",  "us/pacific")
        await preferences.set_name.__call__(preferences, ctx_user2, "alias2", "utc")
        await preferences.set_name.__call__(preferences, ctx_user3, "alias3", "invalidTZ")

        all_prefs = await preferences.cortex.get_memory(Memory.PREFERENCES)
        assert len(all_prefs.items()) == 2

        # set time only
        await preferences.set_timezone.__call__(preferences, ctx_user3, "us/pacific")
        all_prefs = await preferences.cortex.get_memory(Memory.PREFERENCES)
        assert len(all_prefs.items()) == 3

    @pytest.mark.asyncio
    async def test_list(self, preferences, ctx_user1, ctx_user3):


        # list user preferences
        await preferences.list_preferences.__call__(preferences, ctx_user1)

        # Assert on embed properties
        ctx_user1.send.assert_called_once()
        embed = ctx_user1.send.call_args.kwargs.get('embed')
        assert len(embed.fields) == 3

