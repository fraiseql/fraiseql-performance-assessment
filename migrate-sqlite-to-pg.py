#!/usr/bin/env python3
"""Migrate data from SQLite to PostgreSQL with CQRS schema mapping."""

import sqlite3
import sys
from pathlib import Path
from uuid import UUID
from datetime import datetime
import psycopg

def migrate_sqlite_to_pg(sqlite_path: str, pg_host: str = "localhost", pg_port: int = 5435, pg_db: str = "fraiseql_benchmark", pg_user: str = "benchmark", pg_password: str = "benchmark123"):
    """Migrate data from SQLite database to PostgreSQL with CQRS schema mapping."""

    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        return False

    print(f"📦 Starting migration from {sqlite_path.name}...")

    try:
        # Connect to both databases
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()

        pg_conn = psycopg.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            dbname=pg_db
        )
        pg_cursor = pg_conn.cursor()

        # Table mappings from SQLite to PostgreSQL CQRS
        migrations = {
            "users": {
                "pg_table": "tb_user",
                "columns": {
                    "pk_user": "pk_user",
                    "id": "id",
                    "identifier": "identifier",
                    "email": "email",
                    "username": "username",
                    "full_name": "full_name",
                    "bio": "bio",
                    "created_at": "created_at",
                    "updated_at": "updated_at"
                },
                "transforms": {
                    "id": lambda x: UUID(x) if isinstance(x, str) else x,
                    "created_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x,
                    "updated_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x
                }
            },
            "posts": {
                "pg_table": "tb_post",
                "columns": {
                    "pk_post": "pk_post",
                    "id": "id",
                    "identifier": "identifier",
                    "fk_author": "fk_author",
                    "title": "title",
                    "content": "content",
                    "published": "published",
                    "created_at": "created_at",
                    "updated_at": "updated_at"
                },
                "transforms": {
                    "id": lambda x: UUID(x) if isinstance(x, str) else x,
                    "created_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x,
                    "updated_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x,
                    "published": lambda x: datetime.fromisoformat(x) if isinstance(x, str) and x else x
                }
            },
            "comments": {
                "pg_table": "tb_comment",
                "columns": {
                    "pk_comment": "pk_comment",
                    "id": "id",
                    "fk_post": "fk_post",
                    "fk_author": "fk_author",
                    "content": "content",
                    "created_at": "created_at",
                    "updated_at": "updated_at"
                },
                "transforms": {
                    "id": lambda x: UUID(x) if isinstance(x, str) else x,
                    "created_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x,
                    "updated_at": lambda x: datetime.fromisoformat(x) if isinstance(x, str) else x
                }
            },
            "post_likes": {
                "pg_table": "tb_post_like",
                "columns": {
                    "pk_post_like": "pk_post_like",
                    "fk_post": "fk_post",
                    "fk_user": "fk_user"
                },
                "transforms": {}
            },
            "user_follows": {
                "pg_table": "tb_user_follows",
                "columns": {
                    "pk_user_follows": "pk_user_follows",
                    "fk_follower": "fk_follower",
                    "fk_following": "fk_following"
                },
                "transforms": {}
            }
        }

        for sqlite_table, mapping in migrations.items():
            pg_table = mapping["pg_table"]
            print(f"\n📋 Migrating {sqlite_table} → {pg_table}")

            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
            rows = sqlite_cursor.fetchall()

            if not rows:
                print(f"   ⚠️  No data in {sqlite_table}")
                continue

            # Get column info
            sqlite_cursor.execute(f"PRAGMA table_info({sqlite_table})")
            sqlite_cols = [row[1] for row in sqlite_cursor.fetchall()]

            # Clear existing data
            pg_cursor.execute(f"TRUNCATE TABLE {pg_table} CASCADE")

            # Transform and insert rows
            pg_cols = [mapping["columns"][col] for col in sqlite_cols]
            transforms = mapping["transforms"]

            transformed_rows = []
            for row in rows:
                transformed_row = []
                for i, (sqlite_col, val) in enumerate(zip(sqlite_cols, row)):
                    if sqlite_col in transforms and val is not None:
                        val = transforms[sqlite_col](val)
                    transformed_row.append(val)
                transformed_rows.append(tuple(transformed_row))

            # Insert transformed data (using OVERRIDING SYSTEM VALUE for identity columns)
            col_names = ", ".join(pg_cols)
            placeholders = ", ".join(["%s"] * len(pg_cols))
            insert_sql = f"INSERT INTO {pg_table} ({col_names}) OVERRIDING SYSTEM VALUE VALUES ({placeholders})"

            pg_cursor.executemany(insert_sql, transformed_rows)
            pg_conn.commit()

            print(f"   ✓ Migrated {len(transformed_rows)} records")

        # Close connections
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

        print(f"\n✅ Migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sqlite_file = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_small.db"
    success = migrate_sqlite_to_pg(sqlite_file)
    sys.exit(0 if success else 1)
