#!/usr/bin/env python3
"""Run SQL migrations against the database."""

import asyncio
import glob
import os
import sys

import asyncpg

DATABASE_URL = os.environ.get("DATABASE_URL", "")


async def run():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL is not set")
        sys.exit(1)

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Ensure migration tracking table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        applied = {
            r["version"]
            for r in await conn.fetch("SELECT version FROM schema_migrations")
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
            await conn.execute(sql)
            print(f"  OK {version}")

        print("All migrations applied.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
