#!/bin/bash
# Database backup script
# Usage: ./scripts/backup.sh
# Requires: DATABASE_URL and BACKUP_DIR env vars

set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_DIR:=/backups}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $FILENAME"
pg_dump "$DATABASE_URL" | gzip > "$FILENAME"
echo "Backup complete: $FILENAME"

# Keep only last 30 backups
cd "$BACKUP_DIR" && ls -t backup_*.sql.gz | tail -n +31 | xargs -r rm --
echo "Cleanup done. Backups retained: $(ls backup_*.sql.gz | wc -l)"
