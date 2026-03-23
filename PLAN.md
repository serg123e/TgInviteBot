# Telegram Onboarding Bot — Implementation Plan

This document describes the architecture, data model, and step-by-step implementation plan for the bot. It can be used to reproduce the project from scratch.

## Clarifications to the Original Spec

### Assumptions

- **OpenAI API** — used to validate responses (meaningfulness, not spam/junk)
- **Welcome message** — sent directly to the group, stays in chat
- **Management** — Telegram commands in a dedicated admin chat only, no web panel
- **Multi-chat** — one bot instance serves many groups, each with independent settings
- **Admin chat** — one shared chat for all groups; receives notifications about new members

### Components Added Beyond Original Spec

1. **`chat_settings` table** — per-chat configuration (welcome text, timeout, min length, etc.)
2. **AI validation** — OpenAI evaluates whether a response is a meaningful introduction
3. **Rate limiting** — message send queue to avoid Telegram flood control (429 errors)
4. **Backup/restore scripts** — SQLite backup with rotation (last 30 copies)
5. **SQL migrations** — versioned `.sql` files with a Python runner

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | Per requirements |
| Bot framework | aiogram 3.x | Async, mature, middleware + routers |
| Database | SQLite | File-based, zero-config, easy to deploy |
| DB client | aiosqlite | Async wrapper over sqlite3 |
| Timers | APScheduler 3.10+ | Persistent jobs, lighter than Celery |
| AI | OpenAI API (gpt-4o-mini) | Cheap and fast for text validation |
| Config | python-dotenv + DB | Global in `.env`, per-chat in `chat_settings` |
| Validation | Pydantic 2.5+ | Config and data validation |
| Backups | sqlite3 `.backup` + cron | Simple and reliable |

---

## Data Model

### Table: `chat_settings`

```sql
CREATE TABLE chat_settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     INTEGER UNIQUE NOT NULL,
    chat_title  TEXT,
    welcome_text TEXT NOT NULL DEFAULT 'Здравствуйте! Представьтесь, пожалуйста, в течение {timeout} минут: напишите кто вы и чем занимаетесь.',
    timeout_minutes   INTEGER NOT NULL DEFAULT 15,
    min_response_length INTEGER NOT NULL DEFAULT 10,
    ai_validation_enabled INTEGER NOT NULL DEFAULT 1,
    ban_on_remove     INTEGER NOT NULL DEFAULT 0,
    ban_duration_hours INTEGER DEFAULT NULL,   -- NULL = permanent ban when ban_on_remove=1
    whitelist_enabled INTEGER NOT NULL DEFAULT 1,
    ignore_bots       INTEGER NOT NULL DEFAULT 1,
    is_active         INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Table: `group_members`

```sql
CREATE TABLE group_members (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id           INTEGER NOT NULL,
    telegram_user_id  INTEGER NOT NULL,
    username          TEXT,
    first_name        TEXT,
    last_name         TEXT,
    joined_at         TEXT NOT NULL DEFAULT (datetime('now')),
    prompt_sent_at    TEXT,
    prompt_message_id INTEGER,          -- for deleting the welcome message later
    response_text     TEXT,
    responded_at      TEXT,
    ai_validation_result TEXT,          -- JSON string: {"valid": bool, "reason": "..."}
    status            TEXT NOT NULL DEFAULT 'joined',
    removed_at        TEXT,
    removal_reason    TEXT,
    is_whitelisted    INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chat_id, telegram_user_id)
);
```

### Table: `event_logs`

```sql
CREATE TABLE event_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id          INTEGER,
    telegram_user_id INTEGER,
    event_type       TEXT NOT NULL,
    details          TEXT,              -- JSON string
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Indexes

```sql
CREATE INDEX idx_members_chat_status ON group_members(chat_id, status);
CREATE INDEX idx_members_chat_user   ON group_members(chat_id, telegram_user_id);
CREATE INDEX idx_events_chat         ON event_logs(chat_id, created_at);
```

### Member Statuses

| Status | Meaning |
|--------|---------|
| `joined` | Entered the group |
| `prompt_sent` | Welcome message sent |
| `approved` | Passed validation (auto or manual) |
| `rejected` | Failed AI validation, awaiting admin decision |
| `removed_timeout` | Removed for not responding in time |
| `removed_rejected` | Removed after admin confirmed rejection |
| `removed_manual` | Removed by admin directly |
| `left` | Left the group voluntarily |
| `error` | Processing error |

---

## Project Structure

```
TgInviteBot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point: dispatcher, lifecycle, router registration
│   ├── config.py            # Load .env, global settings (Pydantic)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py    # aiosqlite connection (WAL mode)
│   │   ├── members.py       # CRUD for group_members
│   │   ├── settings.py      # CRUD for chat_settings
│   │   └── events.py        # Insert into event_logs
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── new_member.py    # chat_member update → new member detected
│   │   ├── message.py       # Text messages (onboarding responses) + /chatid
│   │   ├── member_left.py   # chat_member update → member left
│   │   └── admin.py         # Admin commands + inline button callbacks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── onboarding.py    # Core workflow: handle_new_member, handle_response,
│   │   │                    #   handle_timeout, approve_member, remove_member,
│   │   │                    #   restore_timers
│   │   ├── scheduler.py     # APScheduler: schedule_removal, cancel_removal
│   │   ├── ai_validator.py  # OpenAI: validate_response → {"valid", "reason"}
│   │   └── notifier.py      # Admin chat: notify_new_member, notify_response,
│   │                        #   notify_timeout (with inline buttons)
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── rate_limit.py    # 50ms minimum interval between handler calls
│   └── utils/
│       ├── __init__.py
│       └── template.py      # Simple {key} placeholder substitution
├── migrations/
│   ├── 001_initial.sql      # Schema: 3 tables + 3 indexes
│   └── run_migrations.py    # Reads SQL files, tracks applied via _migrations table
├── scripts/
│   ├── backup.sh            # sqlite3 .backup, keeps last 30 copies
│   └── restore.sh           # Copies backup file to SQLITE_PATH
├── tests/
│   ├── test_onboarding.py   # Bot-ignoring, whitelist bypass
│   ├── test_ai_validator.py # No API key, valid/invalid responses
│   └── test_template.py     # Placeholder rendering
├── .env.example
├── requirements.txt
├── Dockerfile               # Python 3.11-slim, /app/data volume
├── docker-compose.yml       # Single service, volume for SQLite
├── README.md                # English documentation
├── DEPLOY.md                # Deployment guide (systemd, Docker, cron)
└── PLAN.md                  # This file
```

---

## Environment Variables

```env
# Telegram
BOT_TOKEN=                          # required — from @BotFather
ADMIN_CHAT_ID=                      # required — chat ID for admin notifications

# Database
SQLITE_PATH=data/bot.db             # optional — default: data/bot.db

# OpenAI
OPENAI_API_KEY=                     # optional — without it, AI validation is disabled
OPENAI_MODEL=gpt-4o-mini            # optional — default: gpt-4o-mini

# Defaults (can be overridden per-chat via /config command)
DEFAULT_TIMEOUT_MINUTES=15
DEFAULT_MIN_RESPONSE_LENGTH=10
DEFAULT_AI_VALIDATION=true
DEFAULT_WHITELIST_ENABLED=true
DEFAULT_BAN_ON_REMOVE=false
```

---

## Implementation Steps

### Phase 1: Foundation

1. Initialize project: `requirements.txt`, `.env.example`, `config.py` (Pydantic settings)
2. Set up aiosqlite connection (`bot/db/connection.py`) with WAL mode
3. Create SQL migration (`migrations/001_initial.sql`) — 3 tables, 3 indexes
4. Write migration runner (`migrations/run_migrations.py`) — tracks via `_migrations` table
5. Basic aiogram 3 bot (`bot/main.py`) — dispatcher, startup/shutdown lifecycle, router registration

### Phase 2: Core Onboarding Flow

6. New member handler (`bot/handlers/new_member.py`) — detect via `chat_member` update
7. Welcome message with template rendering (`bot/utils/template.py`) — `{timeout}` placeholder
8. APScheduler integration (`bot/services/scheduler.py`) — `schedule_removal()`, `cancel_removal()`
9. Message handler (`bot/handlers/message.py`) — detect text responses from pending users
10. Timeout handler — remove user, delete welcome message, log event
11. Save response to DB, update status

### Phase 3: AI Validation

12. OpenAI integration (`bot/services/ai_validator.py`):
    - System prompt: evaluate if text is a meaningful introduction
    - Response format: `{"valid": true/false, "reason": "brief explanation"}`
    - Temperature: 0.1 for deterministic output
    - Graceful fallback: auto-approve on API error, missing key, or JSON parse failure
13. Validation logic: `valid=true` → `approved`; `valid=false` → `rejected` + admin notification

### Phase 4: Multi-Chat + Admin Notifications

14. Per-chat settings CRUD (`bot/db/settings.py`) — `get_or_create()`, `update()`
15. Admin notifications (`bot/services/notifier.py`):
    - `notify_new_member()` — user joined, prompt sent
    - `notify_response()` — user replied, with inline buttons (Approve / Remove / Ban)
    - `notify_timeout()` — user removed for inactivity
16. Inline button callbacks in `bot/handlers/admin.py` — parse `action:chat_id:user_id`

### Phase 5: Admin Commands

All commands restricted to `ADMIN_CHAT_ID`:

17. `/pending [chat_id]` — list members with `joined` / `prompt_sent` status
18. `/approve <chat_id> <user_id>` — manually approve a member
19. `/remove <chat_id> <user_id>` — kick a member
20. `/ban <chat_id> <user_id>` — ban a member (respects `ban_duration_hours`)
21. `/whitelist <chat_id> <user_id>` — add to whitelist
22. `/status <chat_id> <user_id>` — show onboarding status details
23. `/config <chat_id> [key=value ...]` — view or update chat settings
24. `/chatid` — user command, works in any chat, shows the chat ID

### Phase 6: Whitelist + Edge Cases

25. Whitelist logic — skip onboarding for returning members (when `whitelist_enabled`)
26. Member left handler (`bot/handlers/member_left.py`) — update status to `left`, cancel timer
27. Re-entry handling — `upsert_member()` resets status and clears previous response
28. Timer recovery after restart — `restore_timers()` on startup:
    - Query all `joined`/`prompt_sent` members
    - Calculate remaining time: `timeout - (now - joined_at)`
    - If remaining > 0: reschedule timer
    - If expired: remove immediately

### Phase 7: Infrastructure

29. Rate limiting middleware (`bot/middlewares/rate_limit.py`) — 50ms async lock
30. Backup script (`scripts/backup.sh`) — `sqlite3 $DB .backup`, rotate last 30
31. Restore script (`scripts/restore.sh`) — copy backup to `SQLITE_PATH`
32. Dockerfile — Python 3.11-slim, `/app/data` directory, run `python -m bot.main`
33. docker-compose.yml — single service, named volume for SQLite persistence

### Phase 8: Testing

34. `tests/test_template.py` — placeholder rendering (basic, multiple, missing keys)
35. `tests/test_ai_validator.py` — mock OpenAI (no key, valid, invalid responses)
36. `tests/test_onboarding.py` — mock bot + DB (ignore bots, whitelist bypass)

### Phase 9: Documentation

37. `README.md` — features, quick start, env vars, commands, database, project structure, comparison with alternatives
38. `DEPLOY.md` — systemd service, Docker, cron backups, update procedure
39. `.env.example` — annotated environment template

---

## Key Design Decisions

### How does the bot recognize an onboarding response?

Any **text message** from a user with status `joined` or `prompt_sent` in that chat is treated as their introduction. It doesn't have to be a reply to the welcome message — just the first text message. Non-text content (stickers, photos, voice) is ignored with a reminder to write text.

### How does AI validation work?

System prompt for GPT-4o-mini:
```
You are a group moderator. A user joined and must introduce themselves.
Evaluate whether the text is a meaningful introduction (name, occupation, reason for joining).
Reply with ONLY valid JSON without markdown: {"valid": true/false, "reason": "brief explanation"}
```

- `valid=true` → status set to `approved`
- `valid=false` → status set to `rejected`, admin notified with action buttons
- API error / missing key / parse failure → auto-approve (graceful degradation)

### How do timers survive a bot restart?

On startup, `restore_timers()` queries the DB for all members with `joined` or `prompt_sent` status. For each:
- Calculate elapsed time: `now - joined_at`
- If `elapsed < timeout` → schedule removal after `timeout - elapsed`
- If `elapsed >= timeout` → execute removal immediately

### Rate limiting strategy

A simple async-lock middleware enforces a minimum 50ms gap between handler executions. This keeps the bot under Telegram's ~30 messages/second limit. On 429 errors from the Telegram API, aiogram handles retry automatically.

### Why SQLite instead of PostgreSQL?

- Zero-config: no database server to install or manage
- Single-file: trivial backups (`sqlite3 .backup`), easy to migrate
- Sufficient performance: a single bot instance handles the expected load
- WAL mode: enables concurrent reads during writes

### Router registration order

In `main.py`, routers are registered in this order:
1. `new_member` — chat_member updates (new member)
2. `member_left` — chat_member updates (member left)
3. `admin` — admin commands (filtered by chat ID)
4. `message` — **must be last** — catch-all for text messages

The message router is last because it acts as a catch-all for text in groups.

---

## Dependencies

```
aiogram>=3.4,<4.0
aiosqlite>=0.19,<1.0
apscheduler>=3.10,<4.0
openai>=1.12,<2.0
python-dotenv>=1.0,<2.0
pydantic>=2.5,<3.0
```

Dev dependencies (not in `requirements.txt`):
```
pytest
pytest-asyncio
```
