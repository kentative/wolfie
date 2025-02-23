"""
Pytest configuration and fixtures
"""
import pytest
import discord
from discord.ext import commands

from typing import List

class MockCommand:
    def __init__(self, name: str):
        self.name = name
        self.qualified_name = name
        self.checks = []
        self.callback = None

    async def __call__(self, *args, **kwargs):
        if self.callback:
            return await self.callback(*args, **kwargs)

    def add_check(self, check):
        self.checks.append(check)

class MockBot:
    def __init__(self):
        self.user = discord.Object(id=1)
        self.command_prefix = "!"
        self.commands: List[commands.Command] = []

    async def get_prefix(self, message):
        return self.command_prefix

    @staticmethod
    async def get_context(message):
        return MockContext()

class MockGuild:
    def __init__(self):
        self.id = 1
        self.name = "Test Guild"

class MockRole:
    def __init__(self, name):
        self.name = name

class MockMember:
    def __init__(self, mock_id=1, name="test_user", roles=None, is_admin=False):
        self.id = mock_id
        self.name = name
        self.display_name = "test_display_name"
        self.roles = roles or []
        self.guild_permissions = discord.Permissions()
        self.guild_permissions.update(manage_guild=is_admin)
        self.bot = False

class MockContext:
    def __init__(self, user_id=1, username="test_user", is_admin=False, roles=None):
        self.bot = MockBot()
        self.guild = MockGuild()
        self.author = MockMember(mock_id=user_id, name=username, roles=roles, is_admin=is_admin)
        self.message = None
        self.sent_messages = []
        self.suggestions_provided = False
        self.valid = False  # Added for suggestion wizard tests
        self.command = None

    async def send(self, content=None, embed=None):
        message = content if content else f"Embed: {embed.title if embed else 'No title'}"
        self.sent_messages.append(message)
        return message

@pytest.fixture
def bot():
    return MockBot()

@pytest.fixture
def ctx_user1():
    return MockContext(
        user_id=1,
        username="user1"
    )

@pytest.fixture
def ctx_user2():
    return MockContext(user_id=2, username="user2")

@pytest.fixture
def ctx_user3():
    return MockContext(user_id=3, username="user3")

@pytest.fixture
def admin_ctx():
    return MockContext(is_admin=True)

@pytest.fixture
def leadership_ctx():
    roles = [MockRole("leadership")]
    return MockContext(roles=roles)
