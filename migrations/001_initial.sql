-- Migration 001: Initial schema (SQLite)

CREATE TABLE IF NOT EXISTS chat_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE NOT NULL,
    chat_title TEXT,
    welcome_text TEXT NOT NULL DEFAULT 'Здравствуйте, {user}! Представьтесь, пожалуйста, в течение {timeout} минут: напишите кто вы, чем занимаетесь и зачем пришли в группу.',
    timeout_minutes INTEGER NOT NULL DEFAULT 30,
    min_response_length INTEGER NOT NULL DEFAULT 50,
    ai_validation_enabled INTEGER NOT NULL DEFAULT 1,
    ban_on_remove INTEGER NOT NULL DEFAULT 0,
    ignore_bots INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    prompt_sent_at TEXT,
    prompt_message_id INTEGER,
    admin_message_id INTEGER,
    response_text TEXT,
    responded_at TEXT,
    ai_validation_result TEXT,
    status TEXT NOT NULL DEFAULT 'joined',
    removed_at TEXT,
    removal_reason TEXT,
    is_whitelisted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chat_id, telegram_user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_members_chat_status ON group_members (chat_id, status);

-- Migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_initial');
