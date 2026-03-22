#!/bin/bash
# Database restore script
# Usage: ./scripts/restore.sh <backup_file> [target_database_url]

set -euo pipefail

BACKUP_FILE="${1:?Usage: restore.sh <backup_file> [target_database_url]}"
TARGET_URL="${2:-${DATABASE_URL:?DATABASE_URL is required}}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: File not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"
echo "Target: $TARGET_URL"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql "$TARGET_URL"
else
    psql "$TARGET_URL" < "$BACKUP_FILE"
fi

echo "Restore complete."
