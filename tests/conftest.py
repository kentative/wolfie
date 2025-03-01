"""
Pytest configuration and fixtures
"""
from typing import List
from unittest.mock import AsyncMock

import discord
import pytest
from discord.ext import commands

from core.cortex import Cortex


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
        self.cortex = Cortex()

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
    def __init__(self, user_id=1, display_name="display_name", name="user", roles=None, is_admin=False):
        self.id = user_id
        self.name = name
        self.display_name = display_name
        self.roles = roles or []
        self.guild_permissions = discord.Permissions()
        self.guild_permissions.update(manage_guild=is_admin)
        self.bot = False

class MockContext:
    def __init__(self, member: MockMember):
        self.bot = MockBot()
        self.guild = MockGuild()
        self.author = member
        self.message = None
        self.sent_messages = []
        self.suggestions_provided = False
        self.valid = False  # Added for suggestion wizard tests
        self.command = None
        self.send = AsyncMock()

    async def send(self, content=None, embed=None):
        message = content if content else f"Embed: {embed.title if embed else 'No title'}"
        self.sent_messages.append(message)
        return message

@pytest.fixture
def bot():
    return MockBot()

@pytest.fixture
def ctx_user1():
    return MockContext(MockMember(
        user_id=1,
        name="user1",
        display_name="display_name1"
    ))

@pytest.fixture
def ctx_user2():
    return MockContext(MockMember(
        user_id=2,
        name="user2",
        display_name="display_name2"
    ))

@pytest.fixture
def ctx_user3():
    return MockContext(MockMember(
        user_id=3,
        name="user3",
        display_name="display_name3"
    ))

@pytest.fixture
def ctx_admin():
    return MockContext(MockMember(
        user_id=1,
        name="user1",
        display_name="display_name1",
        is_admin=True
    ))

@pytest.fixture
def ctx_leadership():
    return MockContext(MockMember(
        user_id=1,
        name="user1",
        display_name="display_name1",
        roles=[MockRole("leadership")]
    ))
