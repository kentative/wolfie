import os
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

from core.brain import Brain
from core.cortex import Cortex
from utils.logger import init_logger

VERSION = "1.2025.03.20-flash"

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')

logger = init_logger('Wolfie')

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = Bot(command_prefix=PREFIX, intents=intents)
bot.cortex = Cortex()
bot.brain = Brain()

@bot.event
async def on_ready():
    logger.info(f'{bot.user} version {VERSION} has connected to Discord!')
    
    # Load all cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:                
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded cog: {filename}')
            except Exception as e:
                logger.error(f'Failed to load cog {filename}: {str(e)}')

    for command in bot.commands:
        bot.brain.register_function(command, command.name, command.help, command.params)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use `{PREFIX}q-help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        traceback.print_exception(type(error), error, error.__traceback__)
        await ctx.send(f'{str(error)}')

if __name__ == '__main__':
    if not TOKEN:
        logger.error("No Discord token found in environment variables!")
        exit(1)
    
    bot.run(TOKEN)


