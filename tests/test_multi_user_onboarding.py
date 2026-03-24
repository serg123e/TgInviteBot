"""Tests for multi-user onboarding using real DB, mocking only Telegram API and OpenAI."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from bot.db import members, settings
from bot.services.onboarding import handle_new_member, handle_response

CHAT_ID = -100999888777
CHAT_TITLE = "Test Group"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_bot(admin_msg_id_seq=None):
    """Create a mock bot. admin_msg_id_seq is an iterator of message_ids for send_message."""
    bot = AsyncMock()
    seq = iter(admin_msg_id_seq or range(1, 1000))
    bot.send_message.return_value = MagicMock(message_id=0)

    # Each send_message returns a unique message_id
    async def _send(chat_id, text, **kw):
        msg = MagicMock()
        msg.message_id = next(seq)
        return msg

    bot.send_message.side_effect = _send
    return bot


async def join(bot, user_id, username=None):
    await handle_new_member(
        bot=bot, chat_id=CHAT_ID, chat_title=CHAT_TITLE,
        user_id=user_id, username=username or f"user{user_id}",
        first_name=f"User{user_id}", last_name=None, is_bot=False,
    )


async def respond(bot, user_id, text, username=None):
    await handle_response(
        bot=bot, chat_id=CHAT_ID, chat_title=CHAT_TITLE,
        user_id=user_id, username=username or f"user{user_id}",
        first_name=f"User{user_id}", text=text,
    )


async def get_member(user_id: int) -> members.GroupMember:
    """Get member from DB, assert it exists."""
    m = await members.get_member(CHAT_ID, user_id)
    assert m is not None, f"Member {user_id} not found in DB"
    return m


@pytest_asyncio.fixture(autouse=True)
async def setup_chat(db):
    """Create chat_settings with low min_response_length for tests."""
    await settings.get_or_create(CHAT_ID, CHAT_TITLE)
    await settings.update(CHAT_ID, min_response_length=10, timeout_minutes=15)


@pytest.fixture
def patches():
    """Mock only external services: Telegram notifications, AI, scheduler."""
    notify_response_calls = []

    async def _notify_response(bot, chat_id, chat_title, user_id, username,
                                first_name, text, ai_result, admin_message_id=None):
        notify_response_calls.append({
            "user_id": user_id,
            "admin_message_id": admin_message_id,
            "ai_result": ai_result,
        })

    with patch("bot.services.onboarding.notifier.notify_new_member", new_callable=AsyncMock) as notify_new, \
         patch("bot.services.onboarding.notifier.notify_response", side_effect=_notify_response), \
         patch("bot.services.onboarding.ai_validator.validate_response", new_callable=AsyncMock) as ai_mock, \
         patch("bot.services.onboarding.schedule_removal") as sched, \
         patch("bot.services.onboarding.cancel_removal"):

        # notify_new_member returns incrementing admin_message_ids
        _counter = iter(range(100, 10000, 100))
        notify_new.side_effect = lambda *a, **kw: next(_counter)

        # Default AI: approve
        ai_mock.return_value = {"valid": True, "reason": "OK"}

        yield {
            "notify_new": notify_new,
            "notify_response_calls": notify_response_calls,
            "ai_mock": ai_mock,
            "schedule": sched,
        }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_each_user_gets_unique_admin_message_id(db, patches):
    """Three users join — each gets a distinct admin_message_id stored in DB."""
    bot = make_bot()
    for uid in [1001, 1002, 1003]:
        await join(bot, uid)

    ids = []
    for uid in [1001, 1002, 1003]:
        m = await get_member(uid)
        assert m is not None
        assert m.status == "prompt_sent"
        ids.append(m.admin_message_id)

    assert len(set(ids)) == 3, "Each user must have a unique admin_message_id"
    assert all(mid is not None for mid in ids)


@pytest.mark.asyncio
async def test_response_uses_correct_admin_message_id(db, patches):
    """When user A responds, notify_response gets A's admin_message_id, not B's."""
    bot = make_bot()
    await join(bot, 2001)
    await join(bot, 2002)

    m1 = await get_member(2001)
    m2 = await get_member(2002)

    await respond(bot, 2001, "Привет! Меня зовут Иван, я Python-разработчик.")
    await respond(bot, 2002, "Здравствуйте! Я Мария, менеджер проектов.")

    calls = {c["user_id"]: c["admin_message_id"] for c in patches["notify_response_calls"]}
    assert calls[2001] == m1.admin_message_id
    assert calls[2002] == m2.admin_message_id


@pytest.mark.asyncio
async def test_ai_approved_sets_status_and_whitelist(db, patches):
    """AI approves → status=approved, is_whitelisted=True in DB."""
    bot = make_bot()
    patches["ai_mock"].return_value = {"valid": True, "reason": "Good intro"}

    await join(bot, 3001)
    await respond(bot, 3001, "Меня зовут Дмитрий, я инженер, пришёл за знаниями.")

    m = await get_member(3001)
    assert m is not None
    assert m.status == "approved"
    assert m.is_whitelisted is True
    assert m.response_text == "Меня зовут Дмитрий, я инженер, пришёл за знаниями."
    assert m.ai_validation_result is not None
    assert m.ai_validation_result["valid"] is True


@pytest.mark.asyncio
async def test_ai_rejected_sets_pending_retry(db, patches):
    """AI rejects → status=pending_retry, timer rescheduled."""
    bot = make_bot()
    patches["ai_mock"].return_value = {"valid": False, "reason": "Нет имени"}

    await join(bot, 3002)
    await respond(bot, 3002, "просто смотрю что тут за группа и для чего она")

    m = await get_member(3002)
    assert m.status == "pending_retry"
    assert m.ai_validation_result is not None
    assert m.ai_validation_result["valid"] is False
    # Timer should be rescheduled (2 calls: initial join + retry)
    assert patches["schedule"].call_count == 2


@pytest.mark.asyncio
async def test_too_short_response_no_status_change(db, patches):
    """Response below min_response_length → status stays prompt_sent."""
    bot = make_bot()
    await join(bot, 3003)

    await respond(bot, 3003, "привет")  # way below 50 chars

    m = await get_member(3003)
    assert m.status == "prompt_sent"
    assert len(patches["notify_response_calls"]) == 0


@pytest.mark.asyncio
async def test_retry_after_rejection_gets_approved(db, patches):
    """After AI rejection, user retries with better text → approved."""
    bot = make_bot()

    await join(bot, 3004)

    # First attempt: rejected
    patches["ai_mock"].return_value = {"valid": False, "reason": "Недостаточно информации"}
    await respond(bot, 3004, "просто посмотреть зашёл, что тут интересного вообще")

    m = await get_member(3004)
    assert m.status == "pending_retry"

    # Second attempt: approved
    patches["ai_mock"].return_value = {"valid": True, "reason": "Хорошее представление"}
    await respond(bot, 3004, "Извините, меня зовут Олег, я дизайнер, интересует UX.")

    m = await get_member(3004)
    assert m.status == "approved"
    assert m.is_whitelisted is True


@pytest.mark.asyncio
async def test_whitelisted_user_skips_onboarding(db, patches):
    """Approved+whitelisted user rejoining skips onboarding entirely."""
    bot = make_bot()

    # First join + approve
    await join(bot, 5001)
    patches["ai_mock"].return_value = {"valid": True, "reason": "OK"}
    await respond(bot, 5001, "Привет! Я Анна, продукт-менеджер, интересуюсь UX.")

    m = await get_member(5001)
    assert m.is_whitelisted is True

    # Reset call counts
    patches["notify_new"].reset_mock()

    # Rejoin — should be skipped
    await join(bot, 5001)
    patches["notify_new"].assert_not_called()


@pytest.mark.asyncio
async def test_concurrent_joins(db, patches):
    """Five users join concurrently — each gets unique admin_message_id, no cross-contamination."""
    bot = make_bot()
    user_ids = [4001, 4002, 4003, 4004, 4005]

    await asyncio.gather(*[join(bot, uid) for uid in user_ids])

    assigned = {}
    for uid in user_ids:
        m = await get_member(uid)
        assert m is not None
        assert m.status == "prompt_sent"
        assigned[uid] = m.admin_message_id

    assert len(set(assigned.values())) == len(user_ids), "admin_message_ids must be unique"

    await asyncio.gather(*[
        respond(bot, uid, f"Привет! Я User{uid}, разработчик, изучаю тему.")
        for uid in user_ids
    ])

    response_map = {c["user_id"]: c["admin_message_id"] for c in patches["notify_response_calls"]}
    for uid in user_ids:
        assert response_map[uid] == assigned[uid], (
            f"User {uid}: expected admin_msg {assigned[uid]}, got {response_map[uid]}"
        )
