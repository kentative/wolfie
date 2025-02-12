import discord
from discord.ext import commands

from core.memory import user_alias
from utils.commons import save_data
from utils.logger import init_logger

NAME_LIST_TITLE = 'Wolfie Name List'

logger = init_logger('Memory')

class WolfieMemory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wolfie.set.name', aliases=['w.set.name'])
    async def set_name(self, ctx, alias:str):
        """Add your alias to Wolfie's name list"""
        embed = discord.Embed(title=NAME_LIST_TITLE,
                              color=discord.Color.dark_embed())

        existing_alias = user_alias.get(str(ctx.author.id), {})
        if existing_alias.get('alias') != alias:
            user_alias[str(ctx.author.id)] = {
                'name': ctx.author.name,
                'alias': alias
            }

            embed.add_field(name=f"{ctx.author.name}", value=f"is known to wolfie as {alias}", inline=False)
            save_data(user_alias, NAME_LIST_PATH)
        else:
            await ctx.send("Wolfie already knows your name")
            return

        await ctx.send(embed=embed)

    @commands.command(name='wolfie.names', aliases=['wolfie.name', 'w.names', 'w.name'])
    async def list_names(self, ctx):
        """Display Wolfie name list"""

        embed = discord.Embed(title=NAME_LIST_TITLE, color=discord.Color.dark_embed())

        for i, value in enumerate(user_alias.values(), start=1):
            embed.add_field(
                name=f"{i}. {value.get('name')}-{value.get('alias')}",
                value="", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WolfieMemory(bot))