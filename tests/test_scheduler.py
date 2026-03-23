"""Tests for scheduler service (asyncio-based)."""

import asyncio

import pytest

from bot.services.scheduler import _tasks, cancel_all, cancel_removal, schedule_removal


@pytest.fixture(autouse=True)
def cleanup_tasks():
    """Clean up scheduler tasks before and after each test."""
    cancel_all()
    yield
    cancel_all()


@pytest.mark.asyncio
async def test_schedule_removal():
    bot = object()
    job_id = schedule_removal(100, 1, 15, bot)
    assert job_id == "removal:100:1"
    assert (100, 1) in _tasks
    assert not _tasks[(100, 1)].done()


@pytest.mark.asyncio
async def test_schedule_removal_replaces_existing():
    bot = object()
    schedule_removal(100, 1, 15, bot)
    old_task = _tasks[(100, 1)]
    schedule_removal(100, 1, 30, bot)
    new_task = _tasks[(100, 1)]
    assert old_task is not new_task
    # Let the event loop process the cancellation
    await asyncio.sleep(0)
    assert old_task.cancelled()


@pytest.mark.asyncio
async def test_cancel_removal_found():
    bot = object()
    schedule_removal(100, 1, 15, bot)
    assert cancel_removal(100, 1) is True
    assert (100, 1) not in _tasks


@pytest.mark.asyncio
async def test_cancel_removal_not_found():
    assert cancel_removal(100, 1) is False


@pytest.mark.asyncio
async def test_cancel_all():
    bot = object()
    schedule_removal(100, 1, 15, bot)
    schedule_removal(200, 2, 15, bot)
    cancel_all()
    assert len(_tasks) == 0


@pytest.mark.asyncio
async def test_schedule_removal_float_timeout():
    bot = object()
    job_id = schedule_removal(100, 1, 7.5, bot)
    assert job_id == "removal:100:1"
