import discord
from discord.ext import commands
from difflib import get_close_matches
from collections import defaultdict, deque
from typing import Dict, Deque, List
from utils.logger import init_logger

logger = init_logger('QueueManager.Suggestion')

class SuggestionWizard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_history: Dict[int, Deque[str]] = defaultdict(lambda: deque(maxlen=10))
        self.context_commands = {
            'queue': {'q-ls', 'q-help', 'q-tribune', 'q-elder', 'q-priest',
                     'q-sage', 'q-master', 'q-praetorian'},
            'admin': {'q-next', 'q-back', 'q-set-time'},
        }

    def get_command_suggestions(self, user_id: int, partial_command: str) -> List[str]:
        """Get command suggestions based on partial input and user history"""
        all_commands = {cmd.name for cmd in self.bot.commands}
        logger.debug(f"Finding suggestions for '{partial_command}' from {len(all_commands)} available commands")

        # Get close matches based on partial command
        matches = get_close_matches(partial_command, all_commands, n=3, cutoff=0.6)
        logger.debug(f"Initial matches: {matches}")

        # Add contextual suggestions based on recent command history
        if user_id in self.command_history:
            recent_commands = self.command_history[user_id]
            logger.debug(f"User command history: {list(recent_commands)}")
            for cmd in recent_commands:
                category = next((cat for cat, cmds in self.context_commands.items()
                               if cmd in cmds), None)
                if category:
                    # Add related commands from the same category
                    matches.extend(list(self.context_commands[category])[:2])
                    logger.debug(f"Added contextual suggestions from {category}: {matches}")

        return list(dict.fromkeys(matches))  # Remove duplicates while preserving order

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages to provide command suggestions"""
        if message.author.bot or not message.content:
            return False

        ctx = await self.bot.get_context(message)
        prefix = await self.bot.get_prefix(message)

        if isinstance(prefix, list):
            prefix = prefix[0]

        # Track command usage in history
        if ctx.valid:
            logger.info(f"User {message.author} executed command: {ctx.command.name}")
            self.command_history[message.author.id].append(ctx.command.name)
            return False  # Allow valid commands to be processed normally

        # Check for potential command attempts (messages starting with prefix)
        elif message.content.startswith(prefix):
            partial_command = message.content[len(prefix):].strip()
            if len(partial_command) >= 2:  # Only suggest for 2+ character inputs
                logger.info(f"Processing suggestion request from {message.author} for: {partial_command}")
                suggestions = self.get_command_suggestions(message.author.id, partial_command)

                if suggestions:
                    suggestion_text = "\n".join([f"`{prefix}{cmd}`" for cmd in suggestions])
                    await message.channel.send(
                        f"Did you mean one of these commands?\n{suggestion_text}"
                    )
                    logger.info(f"Provided suggestions for '{partial_command}' to {message.author}: {suggestions}")
                    # Mark context as handled by suggestion wizard
                    setattr(ctx, 'suggestions_provided', True)
                    return True  # Stop command processing here if we provided suggestions

        return False  # Allow other message events to be processed

async def setup(bot):
    await bot.add_cog(SuggestionWizard(bot))