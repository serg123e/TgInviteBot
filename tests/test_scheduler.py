"""Tests for scheduler service."""

from unittest.mock import MagicMock, patch

import pytest

from bot.services.scheduler import cancel_removal, get_scheduler, schedule_removal


@pytest.fixture
def mock_scheduler():
    sched = MagicMock()
    sched.get_job.return_value = None
    with patch("bot.services.scheduler._scheduler", sched):
        yield sched


def test_get_scheduler_creates_once():
    import bot.services.scheduler as s
    original = s._scheduler
    s._scheduler = None
    sched = get_scheduler()
    assert sched is not None
    sched2 = get_scheduler()
    assert sched is sched2
    s._scheduler = original


def test_schedule_removal(mock_scheduler):
    bot = MagicMock()
    job_id = schedule_removal(100, 1, 15, bot)
    assert job_id == "removal:100:1"
    mock_scheduler.add_job.assert_called_once()


def test_schedule_removal_replaces_existing(mock_scheduler):
    existing_job = MagicMock()
    mock_scheduler.get_job.return_value = existing_job
    bot = MagicMock()
    schedule_removal(100, 1, 15, bot)
    existing_job.remove.assert_called_once()
    mock_scheduler.add_job.assert_called_once()


def test_schedule_removal_float_timeout(mock_scheduler):
    bot = MagicMock()
    job_id = schedule_removal(100, 1, 7.5, bot)
    assert job_id == "removal:100:1"


def test_cancel_removal_found(mock_scheduler):
    job = MagicMock()
    mock_scheduler.get_job.return_value = job
    assert cancel_removal(100, 1) is True
    job.remove.assert_called_once()


def test_cancel_removal_not_found(mock_scheduler):
    mock_scheduler.get_job.return_value = None
    assert cancel_removal(100, 1) is False
