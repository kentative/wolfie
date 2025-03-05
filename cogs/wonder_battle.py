from datetime import datetime

from discord.ext import commands

from cogs.battle.registered_battle import RegisteredBattle, DATE_DISPLAY_FORMAT
from core.ganglia import Memory
from utils.logger import init_logger

BATTLE_NAME = "Wonder Contest"

logger = init_logger('WonderContest')

EMOJIS = {"primary": "⚔️️", "secondary": ""}

class WonderBattle(RegisteredBattle):
    def __init__(self, bot):
        super().__init__(BATTLE_NAME, Memory.WONDER_BATTLE, bot)

    @commands.command(name="wonder.add", aliases=['w.add', 'wonder'])
    async def add(self, ctx,
                     day: str=commands.parameter(description="use d1 or d2"),
                     time: str=commands.parameter(description="use t1, t2 or t3"),
                     options: str=commands.parameter(description="options -p: primary, -s: secondary (default)", default=None)):
        """Register user for a specific day and time slot."""
        if options == '-p' or options == '-s':
            await self.register(ctx, day, time, **{"primary" : options == '-p'})
        elif not options or not isinstance(options, str):
            await self.register(ctx, day, time,  **{"primary" : False})
        else:
            await ctx.send("Invalid options. Use -p for primary.")


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

        await self.list_registration(
            ctx,
            options,
            lambda prefs, entry, user_datetime: self._format_member(prefs, entry, user_datetime))

    @staticmethod
    def _format_member(prefs: dict, entry: dict, user_datetime: datetime):
        primary = EMOJIS["primary"] if entry.get('primary', False) else EMOJIS["secondary"]
        return f'[**{primary}**] {prefs.get("alias", "Unknown")} ({user_datetime.strftime(DATE_DISPLAY_FORMAT)})'


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(WonderBattle(bot))
