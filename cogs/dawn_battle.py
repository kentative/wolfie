from datetime import datetime

from discord.ext import commands
from discord.ext.commands import Context, Command


from cogs.battle.registered_battle import RegisteredBattle, DATE_DISPLAY_FORMAT
from utils.logger import init_logger


BATTLE_NAME = "Battle of Dawn"
REGISTRATION_FILE = "data/dawn_battle_registration.json"
CLASS_NAMES = {
    "Sage": ['cs', 'court', 'sage', 'CourtSage'],
    "ShadowWalker": ['sw', 'shadow', 'walker', 'ShadowWalker'],
    "Monk": ['m', 'monk'],
    "Centurion": ['c', 'ct', 'cent', 'centurion'],
    "Ranger": ['r', 'rg', 'range', 'ranger'],
    "Guardian": ['g', 'guard', 'guardian'],
    "Zealot": ['z', 'zeal', 'zealot'],
    "Magistrate": ['m', 'mag', 'magistrate'],
}
logger = init_logger('DawnBattle')

def find_class(class_input: str):
    # Normalize the input string to lowercase for case-insensitive matching
    input_string = class_input.lower()

    # Iterate through the CLASS_NAMES dictionary
    for class_name, aliases in CLASS_NAMES.items():
        # Check if the input string matches any of the aliases
        if input_string in [alias.lower() for alias in aliases]:
            return class_name

    logger.info(f'class not found: {class_input}')
    return None

class DawnBattle(RegisteredBattle):
    def __init__(self, bot):
        super().__init__(BATTLE_NAME, REGISTRATION_FILE, bot)
        self.wolfie = bot.brain


    @commands.command(name="dawn.test", aliases=['d.test', 'test'])
    async def dawn_test(self, ctx: Context, *question: str):

        dawn_add: Command = ctx.bot.get_command("dawn.add")
        self.wolfie.register_function(
            name=dawn_add.name,
            description=dawn_add.description,
            parameters=dawn_add.params)

        response = self.wolfie.ask(question)
        await ctx.send(response)

    @commands.command(name="dawn.add", aliases=['d.add', 'dawn', 'd'])
    async def add(self, ctx,
                     day: str=commands.parameter(description="use d1 or d2"),
                     time: str=commands.parameter(description="use t1, t2 or t3"),
                     battle_class: str = commands.parameter(description="one of 'CourtSage, ShadowWalker, Monk, Centurion, Ranger, Guardian, Zealot, Magistrate'")):
        """Register user for a specific day and time slot."""
        battle_class = find_class(battle_class)

        if not battle_class:
            await ctx.send(f"Unknown class, please specify one of these `{', '.join(CLASS_NAMES.keys())}`")
            return

        await self.register(ctx, day, time, **{
            "role" : battle_class
        })

    @commands.command(name="dawn.remove", aliases=['d.remove', 'd.rm', 'dawn.rm'])
    async def remove(self, ctx,
                     day: str=commands.parameter(description="use d1 or d2"),
                     time: str=commands.parameter(description="use t1, t2 or t3")):
        """Unregister user for a specific day and time slot."""

        await self.unregister(ctx, day, time)


    async def dawn_set_role(self, ctx,
            battle_class: str,
            power: str,
            troop1: str):
        pass

    @commands.command(name="dawn.list", aliases=['dawn.ls', 'd.ls', 'd.list'])
    async def list(self, ctx, options:str = commands.parameter(description="supported options: 'all'", default="")):
        """List current registration information in UTC."""

        await self.list_registration(ctx, options, lambda prefs, entry, user_datetime: self._format_member(prefs, entry,
                                                                                                           user_datetime))

    @staticmethod
    def _format_member(prefs: dict, entry: dict, user_datetime: datetime):
        context = entry.get('context', {})
        role = context.get('role', 'Unknown')
        return f'[**{role}**] {prefs.get("alias", "Unknown")} ({user_datetime.strftime(DATE_DISPLAY_FORMAT)})'


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(DawnBattle(bot))
