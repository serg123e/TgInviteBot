-- Migration 001: Initial schema

CREATE TABLE IF NOT EXISTS chat_settings (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    chat_title TEXT,
    welcome_text TEXT NOT NULL DEFAULT 'Здравствуйте! Представьтесь, пожалуйста, в течение {timeout} минут: напишите кто вы, чем занимаетесь и зачем пришли в группу.',
    timeout_minutes INT NOT NULL DEFAULT 15,
    min_response_length INT NOT NULL DEFAULT 10,
    ai_validation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ban_on_remove BOOLEAN NOT NULL DEFAULT FALSE,
    ban_duration_hours INT DEFAULT NULL,
    whitelist_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ignore_bots BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    telegram_user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prompt_sent_at TIMESTAMPTZ,
    prompt_message_id BIGINT,
    response_text TEXT,
    responded_at TIMESTAMPTZ,
    ai_validation_result JSONB,
    status TEXT NOT NULL DEFAULT 'joined',
    removed_at TIMESTAMPTZ,
    removal_reason TEXT,
    is_whitelisted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chat_id, telegram_user_id)
);

CREATE TABLE IF NOT EXISTS event_logs (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT,
    telegram_user_id BIGINT,
    event_type TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_members_chat_status ON group_members (chat_id, status);
CREATE INDEX IF NOT EXISTS idx_members_status ON group_members (status) WHERE status IN ('joined', 'prompt_sent');
CREATE INDEX IF NOT EXISTS idx_events_chat ON event_logs (chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON event_logs (event_type, created_at);

-- Migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version) VALUES ('001_initial')
ON CONFLICT DO NOTHING;
