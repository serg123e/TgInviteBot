#!/bin/bash
# Database restore script (SQLite)
# Usage: ./scripts/restore.sh <backup_file> [target_path]

set -euo pipefail

BACKUP_FILE="${1:?Usage: restore.sh <backup_file> [target_path]}"
TARGET="${2:-${SQLITE_PATH:-data/bot.db}}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: File not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"
echo "Target: $TARGET"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

cp "$BACKUP_FILE" "$TARGET"
echo "Restore complete."
