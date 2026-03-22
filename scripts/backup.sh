#!/bin/bash
# Database backup script (SQLite)
# Usage: ./scripts/backup.sh

set -euo pipefail

: "${SQLITE_PATH:=data/bot.db}"
BACKUP_DIR="${BACKUP_DIR:-backups}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/backup_${TIMESTAMP}.db"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $FILENAME"
sqlite3 "$SQLITE_PATH" ".backup '$FILENAME'"
echo "Backup complete: $FILENAME"

# Keep only last 30 backups
cd "$BACKUP_DIR" && ls -t backup_*.db 2>/dev/null | tail -n +31 | xargs -r rm --
echo "Cleanup done. Backups retained: $(ls backup_*.db 2>/dev/null | wc -l)"
