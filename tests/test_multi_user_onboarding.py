"""Tests for multi-user onboarding: concurrent joins, different outcomes,
and correct per-user admin message editing."""
import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.onboarding import handle_new_member, handle_response

CHAT_ID = -100999888777


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cfg(**overrides):
    cfg = MagicMock()
    cfg.is_active = True
    cfg.ignore_bots = True
    cfg.whitelist_enabled = True
    cfg.ai_validation_enabled = True
    cfg.timeout_minutes = 15
    cfg.min_response_length = 10
    cfg.welcome_text = "Представьтесь в течение {timeout} минут."
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def make_member(user_id, status="prompt_sent", admin_message_id=None):
    m = MagicMock()
    m.telegram_user_id = user_id
    m.status = status
    m.admin_message_id = admin_message_id
    m.is_whitelisted = False
    m.prompt_message_id = None
    return m


def make_bot():
    bot = AsyncMock()
    bot.send_message.return_value = MagicMock(message_id=0)
    return bot


# ---------------------------------------------------------------------------
# State tracker: simulates DB state across handle_new_member / handle_response
# ---------------------------------------------------------------------------

class FakeDB:
    """Tracks member state and admin_message_id assignments per user."""

    def __init__(self):
        self.members: dict[int, MagicMock] = {}
        self._notify_counter = 0
        self.notify_new_calls: list[int] = []
        self.notify_response_calls: list[dict] = []

    def next_admin_msg_id(self, user_id: int) -> int:
        self._notify_counter += 1
        msg_id = self._notify_counter * 100
        self.notify_new_calls.append(user_id)
        return msg_id

    def upsert(self, user_id: int) -> MagicMock:
        m = make_member(user_id)
        self.members[user_id] = m
        return m

    def get(self, user_id: int) -> MagicMock | None:
        return self.members.get(user_id)

    async def update_status(self, chat_id, user_id, status, **kwargs):
        m = self.members.get(user_id) or make_member(user_id)
        m.status = status
        if "admin_message_id" in kwargs:
            m.admin_message_id = kwargs["admin_message_id"]
        self.members[user_id] = m
        return m

    async def notify_new_member(self, bot, chat_id, chat_title, user_id, username, first_name):
        return self.next_admin_msg_id(user_id)

    async def notify_response(self, bot, chat_id, chat_title, user_id, username,
                               first_name, text, ai_result, admin_message_id=None):
        self.notify_response_calls.append({
            "user_id": user_id,
            "admin_message_id": admin_message_id,
            "ai_result": ai_result,
        })


def apply_patches(stack: contextlib.ExitStack, db: FakeDB, cfg,
                  ai_result=None, schedule_mock=None):
    """Enter all common patches into the given ExitStack."""
    p = [
        patch("bot.services.onboarding.settings.get_or_create", return_value=cfg),
        patch("bot.services.onboarding.members.get_member",
              side_effect=lambda c, u: db.get(u)),
        patch("bot.services.onboarding.members.upsert_member",
              side_effect=lambda *a, **kw: db.upsert(a[1])),
        patch("bot.services.onboarding.members.update_status",
              side_effect=db.update_status),
        patch("bot.services.onboarding.notifier.notify_new_member",
              side_effect=db.notify_new_member),
        patch("bot.services.onboarding.notifier.notify_response",
              side_effect=db.notify_response),
        patch("bot.services.onboarding.ai_validator.validate_response",
              return_value=ai_result or {"valid": True, "reason": "OK"}),
        patch("bot.services.onboarding.events.log_event", new_callable=AsyncMock),
        patch("bot.services.onboarding.schedule_removal", schedule_mock or MagicMock()),
        patch("bot.services.onboarding.cancel_removal"),
    ]
    for cm in p:
        stack.enter_context(cm)


async def join(db, cfg, bot, user_id):
    await handle_new_member(
        bot=bot, chat_id=CHAT_ID, chat_title="Test Group",
        user_id=user_id, username=f"user{user_id}",
        first_name=f"User{user_id}", last_name=None, is_bot=False,
    )


async def respond(db, cfg, bot, user_id, text):
    await handle_response(
        bot=bot, chat_id=CHAT_ID, chat_title="Test Group",
        user_id=user_id, username=f"user{user_id}", first_name=f"User{user_id}",
        text=text,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_each_user_gets_unique_admin_message_id():
    """Three users join sequentially — each gets a distinct admin_message_id."""
    db = FakeDB()
    cfg = make_cfg()
    bot = make_bot()

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg)
        for uid in [1001, 1002, 1003]:
            await join(db, cfg, bot, uid)

    ids = [db.members[uid].admin_message_id for uid in [1001, 1002, 1003]]
    assert len(set(ids)) == 3, "Each user must have a unique admin_message_id"
    assert all(mid is not None for mid in ids)


@pytest.mark.asyncio
async def test_response_edits_own_admin_message_not_others():
    """When user A responds, notify_response uses A's admin_message_id, not B's."""
    db = FakeDB()
    cfg = make_cfg()
    db.members[2001] = make_member(2001, status="prompt_sent", admin_message_id=111)
    db.members[2002] = make_member(2002, status="prompt_sent", admin_message_id=222)

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg)
        await respond(db, cfg, make_bot(), 2001, "Привет! Меня зовут Иван, я Python-разработчик.")
        await respond(db, cfg, make_bot(), 2002, "Здравствуйте! Я Мария, менеджер проектов.")

    calls = {c["user_id"]: c["admin_message_id"] for c in db.notify_response_calls}
    assert calls[2001] == 111, "User 2001 must reference their own admin message"
    assert calls[2002] == 222, "User 2002 must reference their own admin message"


@pytest.mark.asyncio
async def test_ai_approved_outcome():
    """AI approves response → status=approved, admin notified with valid=True."""
    db = FakeDB()
    cfg = make_cfg()
    db.members[3001] = make_member(3001, status="prompt_sent", admin_message_id=301)

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg, ai_result={"valid": True, "reason": "Хорошее представление"})
        await respond(db, cfg, make_bot(), 3001,
                      "Меня зовут Дмитрий, я инженер, пришёл за знаниями.")

    assert db.members[3001].status == "approved"
    call = db.notify_response_calls[0]
    assert call["ai_result"]["valid"] is True
    assert call["admin_message_id"] == 301


@pytest.mark.asyncio
async def test_ai_rejected_outcome():
    """AI rejects response → status=pending_retry, timer rescheduled, admin notified."""
    db = FakeDB()
    cfg = make_cfg()
    db.members[3002] = make_member(3002, status="prompt_sent", admin_message_id=302)

    schedule_mock = MagicMock()
    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg,
                      ai_result={"valid": False, "reason": "Нет имени и цели"},
                      schedule_mock=schedule_mock)
        await respond(db, cfg, make_bot(), 3002, "просто смотрю что тут за группа")

    assert db.members[3002].status == "pending_retry"
    call = db.notify_response_calls[0]
    assert call["ai_result"]["valid"] is False
    assert call["admin_message_id"] == 302
    schedule_mock.assert_called_once()


@pytest.mark.asyncio
async def test_too_short_response_sends_reminder_no_status_change():
    """Response below min_response_length → reminder sent, status unchanged."""
    db = FakeDB()
    cfg = make_cfg(min_response_length=10)
    db.members[3003] = make_member(3003, status="prompt_sent", admin_message_id=303)

    bot = make_bot()
    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg)
        await respond(db, cfg, bot, 3003, "привет")  # 6 chars < 10

    assert db.members[3003].status == "prompt_sent"
    assert len(db.notify_response_calls) == 0
    bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_pending_retry_user_can_retry_and_get_approved():
    """After AI rejection user sends a better message → gets approved."""
    db = FakeDB()
    cfg = make_cfg()
    db.members[3004] = make_member(3004, status="prompt_sent", admin_message_id=304)

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg,
                      ai_result={"valid": False, "reason": "Недостаточно информации"})
        await respond(db, cfg, make_bot(), 3004, "просто посмотреть зашёл")

    assert db.members[3004].status == "pending_retry"

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg,
                      ai_result={"valid": True, "reason": "Хорошее представление"})
        await respond(db, cfg, make_bot(), 3004,
                      "Извините, меня зовут Олег, я дизайнер, интересует UX.")

    assert db.members[3004].status == "approved"
    assert all(c["admin_message_id"] == 304 for c in db.notify_response_calls)


@pytest.mark.asyncio
async def test_concurrent_joins_no_cross_contamination():
    """Five users join and respond concurrently — each references only their admin_message_id."""
    db = FakeDB()
    cfg = make_cfg()
    bot = make_bot()
    user_ids = [4001, 4002, 4003, 4004, 4005]

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg)
        await asyncio.gather(*[join(db, cfg, bot, uid) for uid in user_ids])

    assigned = {uid: db.members[uid].admin_message_id for uid in user_ids}
    assert all(mid is not None for mid in assigned.values())
    assert len(set(assigned.values())) == len(user_ids), "admin_message_ids must be unique"

    with contextlib.ExitStack() as stack:
        apply_patches(stack, db, cfg, ai_result={"valid": True, "reason": "OK"})
        await asyncio.gather(*[
            respond(db, cfg, bot, uid, f"Привет! Я User{uid}, разработчик, изучаю тему.")
            for uid in user_ids
        ])

    response_map = {c["user_id"]: c["admin_message_id"] for c in db.notify_response_calls}
    for uid in user_ids:
        assert response_map[uid] == assigned[uid], (
            f"User {uid}: notify_response used wrong admin_message_id "
            f"(expected {assigned[uid]}, got {response_map[uid]})"
        )
