#!/usr/bin/env python3
"""Run SQL migrations against SQLite database."""

import glob
import os
import sqlite3
import sys


def run():
    db_path = os.environ.get("SQLITE_PATH", "data/bot.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        # Ensure migration tracking table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

        applied = {
            row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }

        migration_dir = os.path.dirname(os.path.abspath(__file__))
        files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))

        for filepath in files:
            version = os.path.basename(filepath).replace(".sql", "")
            if version in applied:
                print(f"  SKIP {version} (already applied)")
                continue

            print(f"  APPLY {version}...")
            sql = open(filepath).read()
            conn.executescript(sql)
            print(f"  OK {version}")

        print("All migrations applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
