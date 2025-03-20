from discord.ext import commands

from core.cortex import Cortex
from core.ganglia import Memory
from utils.logger import init_logger

NAME_LIST_TITLE = 'Wolfie Name List'

logger = init_logger('Wolfai')

EMOJIS = {"day": "☀️", "night": "💤"}

class Wolfai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cortex: Cortex = bot.cortex
        self.memory = Memory.INTERACTIONS
        self.brain = bot.brain
        self.cortex.initialize_memory(self.memory, {})

    @commands.command(name='wolfie.ask', aliases=['ask', 'w'])
    async def ask(self, ctx, *, question: str=commands.parameter(description="The question you want to ask Wolfie")):
        """
        Ask Wolfie a question.
        """
        logger.info(f"ask: {question}")

        user_id = str(ctx.author.id)
        user_interactions: dict = await self.cortex.get_memory(self.memory, user_id)
        user_details = await self.cortex.get_user_details(user_id)
        user_details.pop("interactions", None)


        interaction_history = user_interactions.get("history", [])
        response = self.brain.ask(user_details, interaction_history, question)

        # update interaction history
        interaction_history.append({
            'question': question,
            'response': response,
        })

        user_interactions.update({
            # retain the last 10 interactions
            "history": interaction_history[-10:] if len(interaction_history) > 10 else interaction_history
        })

        await self.cortex.update_memory(Memory.INTERACTIONS, user_id, user_interactions)
        await self.cortex.remember(self.memory)
        await ctx.send(f"{response}")


async def setup(bot):
    await bot.add_cog(Wolfai(bot))