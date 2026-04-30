from __future__ import annotations

import re
import time

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Database:
    def __init__(self, database_url: str, schema: str) -> None:
        if not SCHEMA_RE.fullmatch(schema):
            raise ValueError(
                "DB_SCHEMA must start with a letter or underscore and contain "
                "only letters, digits and underscores"
            )
        self.database_url = database_url
        self.schema = schema

    def initialize(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(self.schema)
                    )
                )
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.items (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            value TEXT NOT NULL,
                            updated_at DOUBLE PRECISION NOT NULL
                        )
                        """
                    ).format(sql.Identifier(self.schema))
                )

    def count_items(self) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) AS count FROM {}.items").format(
                        sql.Identifier(self.schema)
                    )
                )
                row = cur.fetchone()
                return int(row["count"])

    def ping(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone()
                return row["ok"] == 1

    def reset(self, dataset_size: int) -> None:
        now = time.time()
        rows = [
            (item_id, f"Item {item_id}", f"initial-value-{item_id}", now)
            for item_id in range(1, dataset_size + 1)
        ]
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}.items").format(
                        sql.Identifier(self.schema)
                    )
                )
                cur.executemany(
                    sql.SQL(
                        """
                        INSERT INTO {}.items (id, name, value, updated_at)
                        VALUES (%s, %s, %s, %s)
                        """
                    ).format(sql.Identifier(self.schema)),
                    rows,
                )

    def get_item(self, item_id: int) -> dict | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        SELECT id, name, value, updated_at
                        FROM {}.items
                        WHERE id = %s
                        """
                    ).format(sql.Identifier(self.schema)),
                    (item_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return dict(row)

    def upsert_item(
        self,
        item_id: int,
        value: str,
        name: str | None = None,
        updated_at: float | None = None,
    ) -> dict:
        item_name = name or f"Item {item_id}"
        item_updated_at = updated_at or time.time()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.items (id, name, value, updated_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            value = EXCLUDED.value,
                            updated_at = EXCLUDED.updated_at
                        """
                    ).format(sql.Identifier(self.schema)),
                    (item_id, item_name, value, item_updated_at),
                )
        return {
            "id": item_id,
            "name": item_name,
            "value": value,
            "updated_at": item_updated_at,
        }

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)
