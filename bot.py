import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.commons import load_data
from utils.logger import init_logger

VERSION = "1.0.20250209"

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')

logger = init_logger('Wolfie')

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use `{PREFIX}q-help` to see available cwommands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        logger.error(f'An error occurred: {str(error)}')
        await ctx.send(f'{str(error)}')

if __name__ == '__main__':
    if not TOKEN:
        logger.error("No Discord token found in environment variables!")
        exit(1)
    
    bot.run(TOKEN)
