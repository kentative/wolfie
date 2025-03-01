from discord.ext import commands

from cogs.battle.registered_battle import RegisteredBattle
from utils.logger import init_logger

BATTLE_NAME = "Wonder Contest"
REGISTRATION_FILE = "data/wonder_conquest_teams.json"

logger = init_logger('WonderContest')

class WonderBattle(RegisteredBattle):
    def __init__(self, bot):
        super().__init__(BATTLE_NAME, REGISTRATION_FILE, bot)

    @commands.command(name="wonder.add", aliases=['w.add', 'wonder'])
    async def add(self, ctx,
                     day: str=commands.parameter(description="use d1 or d2"),
                     time: str=commands.parameter(description="use t1, t2 or t3")):
        """Register user for a specific day and time slot."""
        await self.register(ctx, day, time)


    @commands.command(name="wonder.remove", aliases=['wonder.rm'])
    async def remove(self, ctx,
                     day: str=commands.parameter(description="use d1 or d2"),
                     time: str=commands.parameter(description="use t1, t2 or t3")):
        """Unregister user for a specific day and time slot."""
        await self.unregister(ctx, day, time)


    @commands.command(name="wonder.list", aliases=['wonder.ls', 'w.ls', 'w.list'])
    async def wonder_list(self, ctx, options:str = commands.parameter(description="supported options: 'all'", default="")):

        """List current registration information in UTC."""
        await self.list_registration(ctx, options)


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(WonderBattle(bot))
