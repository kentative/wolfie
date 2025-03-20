from datetime import datetime, timezone

import discord
import pytz
from discord.ext import commands

from core.cortex import Cortex
from core.ganglia import Memory
from utils.datetime_utils import DISPLAY_DATE_TIME_FORMAT
from utils.logger import init_logger

NAME_LIST_TITLE = 'Wolfie Name List'

logger = init_logger('Wolfai')

EMOJIS = {"day": "☀️", "night": "💤"}

class Wolfai(commands.Cog):
    def __init__(self, bot):
        self.cortex: Cortex = bot.cortex
        self.memory = Memory.PREFERENCES
        self.brain = bot.brain

    @commands.command(name='wolfie.ask', aliases=['ask'])
    async def ask(self, ctx, *, question: str=commands.parameter(description="The question you want to ask Wolfie")):
        """
        Ask Wolfie a question.
        """

        logger.info(f"ask: {question}")
        response = self.brain.ask(question)
        await ctx.send(f"{response}")


async def setup(bot):
    await bot.add_cog(Wolfai(bot))