-- Migration 002: Add admin_message_id to group_members

ALTER TABLE group_members ADD COLUMN admin_message_id INTEGER;

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('002_admin_message_id');
