import json

import discord
from discord.ext import commands

from utils.logger import init_logger
from utils.commons import save_data, load_data

NAME_LIST_TITLE = 'Wolfie Name List'
NAME_LIST_PATH = "data/names.json"

logger = init_logger('NameList')

class NameList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_alias : dict = load_data(NAME_LIST_PATH)

    @commands.command(name='wolfie.set.name', aliases=['w.set.name'])
    async def set_name(self, ctx, alias:str):
        """Add your alias to Wolfie's name list"""
        embed = discord.Embed(title=NAME_LIST_TITLE,
                              color=discord.Color.dark_embed())

        existing_alias = self.user_alias.get(str(ctx.author.id), {})
        if existing_alias.get('alias') != alias:
            self.user_alias.update({
                ctx.author.id : {
                    'name': ctx.author.name,
                    'alias': alias
                }
            })

            embed.add_field(name=f"{ctx.author.name}", value=f"is known to wolfie as {alias}", inline=False)
            save_data(self.user_alias, NAME_LIST_PATH)
        else:
            await ctx.send("Wolfie already knows your name")
            return

        await ctx.send(embed=embed)

    @commands.command(name='wolfie.names', aliases=['wolfie.name', 'w.names', 'w.name'])
    async def list_names(self, ctx):
        """Display Wolfie name list"""

        embed = discord.Embed(title=NAME_LIST_TITLE, color=discord.Color.dark_embed())

        for i, value in enumerate(self.user_alias.values(), start=1):
            embed.add_field(
                name=f"{i}. {value.get('name')}-{value.get('alias')}",
                value="", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NameList(bot))