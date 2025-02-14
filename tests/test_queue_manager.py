import pytest
from datetime import datetime

import pytest_asyncio
import pytz
from discord.ext import commands
from attached_assets.queue_manager_v1 import QueueManager, has_required_permissions
from tests.conftest import mock_command


@pytest.mark.asyncio
class TestQueueManager:

    @pytest_asyncio.fixture
    async def queue_manager(self, bot, mock_command):
        queue_manager = QueueManager(bot)
        # Set a fixed start time for consistent testing
        queue_manager.queue_start_time = datetime.now(pytz.UTC).replace(
            hour=0, minute=0, second=0, microsecond=0)

        mock_command_callable = mock_command

        # Create and configure commands with proper checks
        queue_manager.advance_queue = commands.Command(mock_command_callable,
                                                 name='advance_queue')
        queue_manager.advance_queue.checks = [has_required_permissions().predicate]
        queue_manager.advance_queue.cog = queue_manager

        queue_manager.rollback_queue = commands.Command(mock_command_callable,
                                                  name='rollback_queue')
        queue_manager.rollback_queue.checks = [has_required_permissions().predicate]
        queue_manager.rollback_queue.cog = queue_manager

        queue_manager.set_queue_time = commands.Command(mock_command_callable,
                                                  name='set_queue_time')
        queue_manager.set_queue_time.checks = [has_required_permissions().predicate]
        queue_manager.set_queue_time.cog = queue_manager

        queue_manager.list_queues = commands.Command(mock_command_callable,
                                               name='list_queues')
        queue_manager.list_queues.cog = queue_manager

        return queue_manager

    async def test_queue_join(self, queue_manager, ctx):
        """Test joining a queue"""
        await queue_manager._add_to_queue(ctx, 'tribune')
        assert len(queue_manager.queues['tribune']) == 1
        assert queue_manager.user_positions[ctx.author.id] == 'tribune'
        assert "Added test_user to the tribune queue" in ctx.sent_messages[0]

    async def test_queue_double_join(self, queue_manager, ctx):
        """Test attempting to join the same queue twice"""
        await queue_manager._add_to_queue(ctx, 'tribune')
        await queue_manager._add_to_queue(ctx, 'tribune')
        assert len(queue_manager.queues['tribune']) == 1
        assert "You are already in the tribune queue" in ctx.sent_messages[1]

    async def test_queue_leave(self, queue_manager, ctx):
        """Test leaving a queue"""
        # First join the queue
        await queue_manager._add_to_queue(ctx, 'tribune')
        assert len(queue_manager.queues['tribune']) == 1

        # Then leave the queue (requires two commands due to confirmation)
        await queue_manager._add_to_queue(
            ctx, 'tribune')  # First attempt triggers confirmation
        await queue_manager._add_to_queue(ctx, 'tribune'
                                          )  # Second attempt confirms leaving

        assert len(queue_manager.queues['tribune']) == 0
        assert ctx.author.id not in queue_manager.user_positions
        assert "removed from the tribune queue" in ctx.sent_messages[-1]

    async def test_queue_multiple_position_join(self, queue_manager, ctx):
        """Test attempting to join multiple queues"""
        await queue_manager._add_to_queue(ctx, 'tribune')
        await queue_manager._add_to_queue(ctx, 'elder')
        assert len(queue_manager.queues['elder']) == 0
        assert "You are already in the tribune queue" in ctx.sent_messages[1]

    @pytest.mark.parametrize(
        "queue_name",
        ['tribune', 'elder', 'priest', 'sage', 'master', 'praetorian'])
    async def test_all_queue_commands(self, queue_manager, ctx, queue_name):
        """Test all queue join commands"""
        await queue_manager._add_to_queue(ctx, queue_name)
        assert len(queue_manager.queues[queue_name]) == 1
        assert queue_manager.user_positions[ctx.author.id] == queue_name

    async def test_advance_queue(self, queue_manager, admin_ctx):
        """Test queue advancement with admin permissions"""
        # First join a queue
        await queue_manager._add_to_queue(admin_ctx, 'tribune')
        # Execute command with proper permission check
        for check in queue_manager.advance_queue.checks:
            assert await check(admin_ctx)
        await queue_manager.advance_queue(admin_ctx)

        assert len(queue_manager.queues['tribune']) == 0
        assert len(queue_manager.processed_queues['tribune_processed']) == 1

    async def test_rollback_queue(self, queue_manager, admin_ctx):
        """Test queue rollback with admin permissions"""
        # First join and advance
        await queue_manager._add_to_queue(admin_ctx, 'tribune')
        await queue_manager.advance_queue(admin_ctx)
        # Then rollback
        await queue_manager.rollback_queue(admin_ctx)

        assert len(queue_manager.queues['tribune']) == 1
        assert len(queue_manager.processed_queues['tribune_processed']) == 0

    async def test_set_queue_time(self, queue_manager, admin_ctx):
        """Test setting queue time with admin permissions"""
        await queue_manager.set_queue_time(admin_ctx, time_str="8")
        assert queue_manager.queue_start_time.hour == 8

    async def test_invalid_queue_time(self, queue_manager, admin_ctx):
        """Test setting invalid queue time with admin permissions"""
        await queue_manager.set_queue_time(admin_ctx, time_str="invalid")
        assert "Invalid time format" in admin_ctx.sent_messages[-1]

    async def test_list_queues(self, queue_manager, ctx):
        """Test queue listing"""
        await queue_manager._add_to_queue(ctx, 'tribune')
        await queue_manager.list_queues(ctx)
        assert any("Queue Status" in msg for msg in ctx.sent_messages)

    async def test_permission_checks(self, queue_manager, ctx, admin_ctx):
        """Test permission checks for admin commands"""
        # Regular user shouldn't be able to advance queue
        for check in queue_manager.advance_queue.checks:
            assert not await check(ctx)

        # Admin should be able to advance queue
        for check in queue_manager.advance_queue.checks:
            assert await check(admin_ctx)
