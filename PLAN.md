# TgInviteBot — Development Plan

How to build this project from scratch. For the current codebase docs, see README.md.

## Goal

A self-hosted Telegram bot that requires new group members to introduce themselves.
Introductions are validated by AI (OpenAI). Members who don't respond are auto-removed.
Admins get notifications with action buttons. One bot instance serves multiple groups.

## Tech choices

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Python 3.11+ | async/await, type hints, fast to prototype |
| Telegram framework | aiogram 3.x | Async, router-based, good typing support |
| Database | SQLite via aiosqlite | Zero setup, file-based, enough for this scale |
| Timers | APScheduler | Reliable, supports crash recovery via DB |
| AI validation | OpenAI API (gpt-4.1-mini) | Cheap, fast, good at structured JSON output |
| Bot mode | Long polling | Simpler than webhooks, no public URL needed |

## Architecture overview

```
handlers/  →  services/onboarding.py  →  db/ (SQLite)
               ├── ai_validator.py        ├── members
               ├── notifier.py            ├── settings
               └── scheduler.py           └── events
```

- **Handlers** receive Telegram events, delegate to services
- **Onboarding service** is the orchestrator — all business logic lives here
- **DB layer** is pure CRUD, no business logic
- **Notifier** sends/edits admin chat messages
- **Scheduler** wraps APScheduler for timeout timers

## Database

3 tables + migration tracker:

- **chat_settings** — per-group config (welcome text, timeout, AI toggle, ban policy)
- **group_members** — per-user state (status, response, AI result, admin_message_id)
- **event_logs** — audit trail
- **schema_migrations** — applied migration versions

Use sequential SQL files (`001_initial.sql`, `002_...`), auto-run on startup.

## Implementation phases

### Phase 1: Skeleton

Set up project structure, config loading from `.env`, DB connection, migration runner.
Create the 3 tables. Verify the bot starts and connects to Telegram.

### Phase 2: Core onboarding flow

The main flow: new member joins → bot sends welcome → timer starts → user responds →
AI validates → approve or reject → timeout kicks.

Build in this order:
1. Detect new member via `chat_member` updates (not service messages — they're unreliable)
2. Send welcome message with timeout mention
3. Schedule removal timer via APScheduler
4. Listen for text responses from pending members
5. Validate response length, then call OpenAI for AI validation
6. Set status to approved/pending_retry based on AI result
7. On timeout: ban + immediate unban (= kick without permanent ban)
8. Allow pending_retry users to try again (treat like "prompt_sent")

### Phase 3: Admin notifications

Send notifications to `ADMIN_CHAT_ID` with inline buttons (Approve / Remove / Ban).

Key UX decision: **edit-in-place** — don't spam the admin chat with multiple messages
per user. Instead:
- "New member" notification → save its `message_id` in DB
- When user responds → edit that same message to show the introduction + AI result + buttons
- On timeout → edit that same message to show timeout info
- Fallback to new message if edit fails (message too old, deleted)

This requires adding `admin_message_id` column to `group_members` (migration 002).

### Phase 4: Admin commands

Add commands that only work in the admin chat:
- `/pending` — list waiting members
- `/approve`, `/remove`, `/ban` — manual actions by chat_id + user_id
- `/whitelist` — skip future onboarding for a member
- `/status` — show member details
- `/config` — view/update per-chat settings

Guard all commands with `F.chat.id == config.admin_chat_id`. Guard callback buttons too.

Add `/chatid` helper for initial setup — it shows the `ADMIN_CHAT_ID=...` line to
copy into `.env`. Disable it once admin chat is configured.

### Phase 5: Resilience

- **Timer recovery**: on startup, load all pending members from DB, calculate remaining
  time, re-schedule or immediately timeout expired ones
- **Rate limiting**: middleware to throttle handler calls
- **Error handling**: catch Telegram API errors in timeout/remove flows, set status to
  "error" instead of crashing

### Phase 6: i18n

Extract all user-facing strings into a translation system:
- English text is the key (doubles as default language)
- `BOT_LANG=ru` loads Russian translations from a dict
- `t("Thanks for the introduction!")` → returns translation or key as-is
- Write a test that auto-scans all `t()` calls and verifies every key has a translation

### Phase 7: Tests

Target: cover all business logic (services, DB, middleware). Handlers are thin wrappers
and lower priority.

- DB tests: use real in-memory SQLite with migrations applied (not mocks)
- Service tests: mock DB and Telegram API, test orchestration logic
- Use `contextlib.ExitStack` for stacking multiple `patch()` context managers
- For multi-user scenarios: build a `FakeDB` class that tracks state across calls

### Phase 8: Release prep

- MIT LICENSE
- `pyproject.toml` with metadata, dev deps, ruff/mypy/pytest config
- `.gitignore` (caches, IDE, .env, PLAN.md)
- `Makefile` (lint, fmt, test, deploy)
- README in English (features, quickstart, env vars, architecture, comparison)
- DEPLOY.md in English (systemd, Docker, backups)
- Dockerfile + docker-compose.yml

## Key design decisions

**How does the bot recognize an onboarding response?**
Any text message from a user with pending status in that chat. It doesn't have to be
a reply to the welcome — just the first text message. Non-text content (stickers, photos)
is ignored with a reminder to write text.

**How does AI validation work?**
System prompt asks GPT to evaluate if the text is a meaningful introduction (name,
occupation, reason). Response: `{"valid": true/false, "reason": "..."}`. On API error,
missing key, or parse failure — auto-approve (graceful degradation).

**Why SQLite?**
Zero-config, single-file backups, WAL mode for concurrent reads. Sufficient for the
expected load of a single bot instance.

**Why long polling instead of webhooks?**
Simpler setup — no public URL, no TLS certificate, no reverse proxy. Latency difference
is negligible for this use case.

**Router registration order matters.**
In `main.py`: new_member → member_left → admin → message. The message router must be
last because it acts as a catch-all for text in groups.

## Pitfalls learned during development

1. **Don't use `~F.text` to filter non-text messages** — it matches service messages
   (joins, leaves). Use an explicit set of `ContentType` values instead.

2. **`only_if_banned=True` in `unban_chat_member` causes race conditions** — if Telegram
   hasn't processed the ban yet, unban silently fails and the user stays banned permanently.
   Remove the flag.

3. **`LANG` env var collides with POSIX** — Linux sets `LANG=en_US.UTF-8` by default.
   Use `BOT_LANG` instead.

4. **`assert` is stripped by `python -O`** — don't use it for runtime validation in
   handlers. Use `if not X: return`.

5. **Saving `admin_message_id` after upsert** — the upsert returns a member with
   `status="joined"`, but by the time you save admin_message_id you need `status="prompt_sent"`.
   Use the literal status string, not `member.status`.

6. **Migration runner must track versions** — `executescript()` doesn't guarantee the
   `INSERT INTO schema_migrations` inside the SQL file runs. Add an explicit
   `INSERT OR IGNORE` after `executescript()` in the runner.

7. **f-strings with `{curly braces}` break `.format()`** — in the i18n system, don't
   call `.format()` when there are no kwargs (the key might contain JSON examples).

## Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `BOT_TOKEN` | yes | — | Telegram bot token from @BotFather |
| `ADMIN_CHAT_ID` | yes | — | Chat ID for admin notifications |
| `BOT_LANG` | no | `en` | Bot language (en, ru) |
| `SQLITE_PATH` | no | `data/bot.db` | Database file path |
| `OPENAI_API_KEY` | no | — | OpenAI key (without it, AI validation disabled, all approved) |
| `OPENAI_MODEL` | no | `gpt-4.1-mini` | OpenAI model |
| `DEFAULT_TIMEOUT_MINUTES` | no | `15` | Response timeout |
| `DEFAULT_MIN_RESPONSE_LENGTH` | no | `10` | Minimum intro length in characters |
| `DEFAULT_AI_VALIDATION` | no | `true` | AI validation on/off |
| `DEFAULT_WHITELIST_ENABLED` | no | `true` | Whitelist feature on/off |
| `DEFAULT_BAN_ON_REMOVE` | no | `false` | Permanent ban vs kick on timeout |
