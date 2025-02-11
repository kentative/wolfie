import pytest
from cogs.suggestion_wizard import SuggestionWizard
import discord
from discord.ext import commands


@pytest.mark.asyncio
class TestSuggestionWizard:

    @pytest.fixture
    def suggestion_wizard(self, bot):
        return SuggestionWizard(bot)

    async def mock_command(*args, **kwargs):
        """Mock coroutine for command callback"""
        pass

    async def test_get_command_suggestions(self, suggestion_wizard):
        """Test command suggestions generation"""
        # Add some command history
        user_id = 1
        suggestion_wizard.command_history[user_id].append('q-tribune')

        # Create mock commands
        suggestion_wizard.bot.commands = [
            MockCommand('q-tribune'),
            MockCommand('q-elder'),
            MockCommand('q-priest'),
        ]

        # Test suggestions for partial command
        suggestions = suggestion_wizard.get_command_suggestions(user_id, 'q-t')
        assert len(suggestions) > 0
        assert any('tribune' in s.lower() for s in suggestions)

    async def test_command_history_tracking(self, suggestion_wizard, ctx):
        """Test command history tracking"""
        user_id = ctx.author.id

        # Simulate command usage
        suggestion_wizard.command_history[user_id].append('q-tribune')
        suggestion_wizard.command_history[user_id].append('q-elder')

        # Check if history is maintained
        assert len(suggestion_wizard.command_history[user_id]) == 2
        assert 'q-tribune' in suggestion_wizard.command_history[user_id]
        assert 'q-elder' in suggestion_wizard.command_history[user_id]

    async def test_contextual_suggestions(self, suggestion_wizard):
        """Test contextual command suggestions"""
        user_id = 1

        # Create mock commands
        suggestion_wizard.bot.commands = [
            MockCommand('q-tribune'),
            MockCommand('q-elder'),
            MockCommand('q-priest'),
            MockCommand('q-sage'),
        ]

        # Add queue-related command to history
        suggestion_wizard.command_history[user_id].append('q-tribune')

        # Get suggestions
        suggestions = suggestion_wizard.get_command_suggestions(user_id, 'q')

        # Should include other queue-related commands
        queue_related = ['elder', 'priest', 'sage']
        assert any(
            any(q in s.lower() for q in queue_related) for s in suggestions)

    async def test_message_handling(self, suggestion_wizard, ctx):
        """Test message handling and suggestion generation"""

        # Create a mock message
        class MockMessage:

            def __init__(self, content, author, bot=False):
                self.content = content
                self.author = author
                self.bot = bot
                self.channel = discord.Object(id=1)
                self.channel.send = self._mock_send

            async def _mock_send(self, content):
                ctx.sent_messages.append(content)
                return content

        # Create mock commands
        suggestion_wizard.bot.commands = [
            MockCommand('q-tribune'),
            MockCommand('q-elder'),
        ]

        # Create mock message with partial command
        message = MockMessage("!q-tr", ctx.author)

        # Process the message
        result = await suggestion_wizard.on_message(message)

        # Check if suggestions were provided
        assert any("tribune" in msg.lower() for msg in ctx.sent_messages)


class MockCommand:

    def __init__(self, name):
        self.name = name
