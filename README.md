# Telegram Onboarding Bot

A bot for automatic onboarding of new members in Telegram groups. It requires newcomers to introduce themselves via text, validates responses using AI (OpenAI), and removes those who fail to respond within the allotted time.

## Features

- **Automatic greeting** of new members with a customizable template
- **AI validation** of responses via OpenAI (gpt-4.1-mini)
- **Removal timer** — automatically removes members who don't introduce themselves
- **Multi-chat** — a single bot instance serves unlimited groups
- **Per-chat settings** — timeout, response length, AI validation, and more
- **Admin chat** — notifications with inline buttons (approve / remove / ban)
- **Whitelist** — returning members skip re-onboarding
- **Timer recovery** after bot restart

## Tech Stack

- Python 3.11+, aiogram 3.x, aiosqlite, APScheduler, OpenAI API
- SQLite (file-based DB, zero-config)

## Quick Start

### 1. Configuration

```bash
cp .env.example .env
# Fill in .env: BOT_TOKEN, ADMIN_CHAT_ID, OPENAI_API_KEY
```

### 2. Migrations

```bash
python -m migrations.run_migrations
```

### 3. Run

```bash
pip install .
python -m bot.main
```

### Docker

```bash
docker-compose up -d
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|:--------:|
| `BOT_TOKEN` | Telegram bot token (from @BotFather) | — | yes |
| `ADMIN_CHAT_ID` | Chat ID for admin notifications | — | yes |
| `BOT_LANG` | Bot language (`en`, `ru`, `hi`, `pt`, `vi`, `id`, `es`) | `en` | no |
| `SQLITE_PATH` | Path to SQLite file | `data/bot.db` | no |
| `OPENAI_API_KEY` | OpenAI API key | — | no* |
| `OPENAI_MODEL` | OpenAI model | `gpt-4.1-mini` | no |
| `DEFAULT_TIMEOUT_MINUTES` | Response timeout in minutes | `15` | no |
| `DEFAULT_MIN_RESPONSE_LENGTH` | Minimum response length | `10` | no |
| `DEFAULT_AI_VALIDATION` | Enable AI validation by default | `true` | no |
| `DEFAULT_WHITELIST_ENABLED` | Enable whitelist by default | `true` | no |
| `DEFAULT_BAN_ON_REMOVE` | Ban instead of kick on removal | `false` | no |

\* Without an API key, AI validation is disabled and all responses are automatically approved.

## How It Works

### Onboarding Flow

1. **New member joins** — the bot detects the event via `chat_member` updates
2. **Whitelist check** — if the member is whitelisted and the feature is enabled, onboarding is skipped
3. **Welcome message** — a customizable greeting is sent, mentioning the user and the timeout
4. **Timer starts** — APScheduler sets a deadline for the member to respond
5. **Admin notified** — a notification is sent to `ADMIN_CHAT_ID`

### Response Handling

1. **Text message received** — the bot checks whether the user has a pending onboarding
2. **Length validation** — the response must meet the minimum length; otherwise the user is reminded
3. **Timer cancelled** — the scheduled removal is stopped
4. **AI validation** — if enabled, OpenAI evaluates whether the text is a meaningful introduction
5. **Status updated** — set to `approved` or `rejected`
6. **Admin notified** — the response is forwarded with action buttons (Approve / Remove / Ban)

### Timeout

1. **Scheduler triggers** — `handle_timeout()` fires at the scheduled time
2. **Ban or kick** — the bot removes the user via the Telegram API
3. **Welcome message deleted** — the original greeting is cleaned up
4. **Event logged** — the action is recorded in the `event_logs` table

## Admin Commands

All commands and inline buttons work only in the admin chat (`ADMIN_CHAT_ID`). They are silently ignored in any other chat.

| Command | Description |
|---------|-------------|
| `/pending [chat_id]` | List members awaiting a response |
| `/approve <chat_id> <user_id>` | Manually approve a member |
| `/remove <chat_id> <user_id>` | Remove (kick) a member |
| `/ban <chat_id> <user_id>` | Ban a member |
| `/whitelist <chat_id> <user_id>` | Add a member to the whitelist |
| `/status <chat_id> <user_id>` | Show a member's onboarding status |
| `/config <chat_id> [key=value ...]` | View or update chat settings |

### User Commands

| Command | Description |
|---------|-------------|
| `/chatid` | Show `ADMIN_CHAT_ID=...` setup instruction (**setup only** — disabled once configured) |

### Configurable Parameters (`/config`)

| Key | Description | Type |
|-----|-------------|------|
| `timeout_minutes` | Response timeout (minutes) | integer |
| `min_response_length` | Minimum response length | integer |
| `ai_validation_enabled` | AI validation | `true` / `false` |
| `ban_on_remove` | Ban on removal instead of kick | `true` / `false` |
| `ban_duration_hours` | Ban duration (number or `null` for permanent) | integer / null |
| `whitelist_enabled` | Whitelist feature | `true` / `false` |
| `ignore_bots` | Ignore bot accounts | `true` / `false` |
| `is_active` | Bot active in this chat | `true` / `false` |
| `welcome_text` | Welcome message template (supports `{timeout}`, `{user}`) | string |

## Localization

The bot supports multiple languages via the `BOT_LANG` environment variable. All user-facing messages are defined as English keys that double as defaults.

| Code | Language | File |
|------|----------|------|
| `en` | English | (default, keys as-is) |
| `ru` | Russian | `bot/i18n/ru.py` |
| `hi` | Hindi | `bot/i18n/hi.py` |
| `pt` | Portuguese | `bot/i18n/pt.py` |
| `vi` | Vietnamese | `bot/i18n/vi.py` |
| `id` | Indonesian | `bot/i18n/id.py` |
| `es` | Spanish | `bot/i18n/es.py` |

To add a new language, create `bot/i18n/<code>.py` with a `MESSAGES` dict mapping English keys to translations, then add the language code to `SUPPORTED_LANGS` in `bot/i18n/__init__.py`. Run `make test` to verify all keys and placeholders are covered.

## Database

The bot uses SQLite with three tables:

- **`chat_settings`** — per-group configuration (timeout, welcome text, feature flags)
- **`group_members`** — individual onboarding state (status, response, AI result, timestamps)
- **`event_logs`** — audit trail of all bot actions

### Member Statuses

| Status | Meaning |
|--------|---------|
| `joined` | User entered the group |
| `prompt_sent` | Welcome message sent |
| `approved` | Passed validation (auto or manual) |
| `pending_retry` | Failed AI validation, can try again |
| `removed_timeout` | Removed for not responding in time |
| `removed_manual` | Removed by admin |
| `left` | User left voluntarily |
| `error` | Processing error occurred |

## Backups

```bash
# Create a backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backups/backup_20260101_120000.db [target_path]
```

Set up automatic daily backups via cron:

```bash
# Run at 3:00 AM daily, keep last 30 backups
0 3 * * * SQLITE_PATH=/path/to/bot.db BACKUP_DIR=/path/to/backups /path/to/scripts/backup.sh
```

## Tests

```bash
pip install '.[dev]'
make test          # Run test suite
make lint          # Run all linters (ruff + mypy + pyright)
make audit         # Check dependencies for known vulnerabilities
make semgrep       # Static analysis (requires: pipx install semgrep)
```

## Project Structure

```
bot/
├── main.py              # Entry point, dispatcher setup
├── config.py            # Configuration (.env loading)
├── db/                  # Database layer
│   ├── connection.py    # aiosqlite connection management
│   ├── members.py       # CRUD for group_members
│   ├── settings.py      # CRUD for chat_settings
│   └── events.py        # Event logging
├── handlers/            # Telegram event handlers
│   ├── new_member.py    # New member joining
│   ├── message.py       # Onboarding responses + /chatid
│   ├── member_left.py   # Member leaving
│   └── admin.py         # Admin commands + inline buttons
├── services/            # Business logic
│   ├── onboarding.py    # Core onboarding workflow
│   ├── scheduler.py     # Timers (APScheduler)
│   ├── ai_validator.py  # OpenAI validation
│   └── notifier.py      # Admin chat notifications
├── i18n/               # Localization
│   ├── __init__.py     # t() translate function, dynamic loader
│   ├── ru.py           # Russian translations
│   ├── hi.py           # Hindi translations
│   ├── pt.py           # Portuguese translations
│   ├── vi.py           # Vietnamese translations
│   ├── id.py           # Indonesian translations
│   └── es.py           # Spanish translations
├── middlewares/
│   └── rate_limit.py    # Rate limiting
└── utils/
    └── template.py      # Template variable substitution

migrations/
├── 001_initial.sql      # Database schema
└── run_migrations.py    # Migration runner

scripts/
├── backup.sh            # SQLite backup (keeps last 30)
└── restore.sh           # Database restore

tests/
├── test_onboarding.py       # Onboarding logic tests
├── test_ai_validator.py     # AI validation tests
├── test_template.py         # Template rendering tests
├── test_i18n.py             # i18n completeness & placeholder tests
└── test_hypothesis.py       # Property-based tests (Hypothesis)
```

## Deployment

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions using systemd or Docker.

## How It Compares

Most Telegram verification bots use CAPTCHA (math puzzles, button clicks, image selection). This bot takes a fundamentally different approach — **meaningful text-based onboarding with AI validation**.

| Feature | This Bot | CAPTCHA Bots | Welcome Bots | SaaS Platforms |
|---------|:--------:|:------------:|:------------:|:--------------:|
| Text-based introduction | Yes | — | — | — |
| AI response validation (LLM) | Yes | — | — | — |
| Auto-removal on timeout | Yes | Yes | — | Partial |
| Whitelist (skip re-onboarding) | Yes | — | — | — |
| Admin inline action buttons | Yes | Partial | Yes | Yes |
| Self-hosted / open-source | Yes | Partial | — | — |
| Per-chat configuration | Yes | Partial | Yes | Yes |
| Timer recovery after restart | Yes | — | N/A | N/A |
| Zero-dependency DB (SQLite) | Yes | Partial | — | — |

### vs CAPTCHA Bots (AntiSpamGlobalBot, Shieldy, JoinCaptchaBot, etc.)

CAPTCHA bots answer "are you human?" — this bot answers "who are you and why are you here?" New members write a real introduction (name, occupation, reason for joining), which is then evaluated by an LLM. This creates a completely different community atmosphere compared to solving a math puzzle.

### vs Welcome Bots (Group Butler, Miss Rose, CodeX Bot)

Welcome bots greet new members but don't require or validate a response. This bot implements the **full cycle**: greeting → waiting for response → AI validation → decision (approve/reject) → auto-removal on timeout.

### vs SaaS Platforms (Metricgram, etc.)

SaaS platforms offer analytics, payments, and gamification but lack AI-powered onboarding validation. This bot is **self-hosted** and **free**, with full control over your data (SQLite, no external services except OpenAI).

## License

MIT License. See [LICENSE](LICENSE) for details.
