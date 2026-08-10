from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised only when dependency is missing.
    psycopg = None
    dict_row = None

from .guard import QueryGuard, translate_qmark_placeholders
from .errors import DatabaseIntegrityError
from .rows import to_db_row
from .schema import SCHEMA_SQL


def _require_psycopg():
    if psycopg is None:
        raise RuntimeError("PostgreSQL DATABASE_URL requires psycopg. Install backend requirements first.")
    return psycopg


class PostgresCursor:
    def __init__(self, cursor) -> None:
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self):
        return to_db_row(self._cursor.fetchone())

    def fetchall(self):
        return [to_db_row(row) for row in self._cursor.fetchall()]

    def __iter__(self):
        for row in self._cursor:
            yield to_db_row(row)


class PostgresConnection:
    dialect = "postgres"

    def __init__(self, connection, guard: QueryGuard) -> None:
        self._connection = connection
        self._guard = guard

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> PostgresCursor:
        values = tuple(params or ())
        self._guard.validate(sql, values)
        cursor = self._connection.cursor()
        try:
            cursor.execute(translate_qmark_placeholders(sql, "%s"), values)
        except _require_psycopg().IntegrityError as exc:
            raise DatabaseIntegrityError(str(exc)) from exc
        return PostgresCursor(cursor)

    def executemany(self, sql: str, params: Iterable[Sequence[Any]]) -> PostgresCursor:
        rows = [tuple(row) for row in params]
        if rows:
            self._guard.validate(sql, rows[0], many=True)
        cursor = self._connection.cursor()
        try:
            cursor.executemany(translate_qmark_placeholders(sql, "%s"), rows)
        except _require_psycopg().IntegrityError as exc:
            raise DatabaseIntegrityError(str(exc)) from exc
        return PostgresCursor(cursor)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class PostgresDatabase:
    def __init__(self, url: str, *, guard: QueryGuard) -> None:
        self.url = url
        self.guard = guard

    def connect(self) -> PostgresConnection:
        pg = _require_psycopg()
        connection = pg.connect(self.url, row_factory=dict_row, autocommit=True)
        return PostgresConnection(connection, self.guard)

    def initialize(self) -> None:
        with self.connect() as connection:
            for statement in _split_statements(SCHEMA_SQL):
                connection.execute(statement)
            self._migrate_existing_schema(connection)

    @staticmethod
    def _columns(connection: PostgresConnection, table: str) -> set[str]:
        rows = connection.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=?",
            (table,),
        )
        return {row[0] for row in rows}

    def _migrate_existing_schema(self, connection: PostgresConnection) -> None:
        additions = {
            "sales_staff": {
                "role": "TEXT NOT NULL DEFAULT 'sales_consultant'",
                "is_active": "INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))",
            },
            "bookings": {"assigned_sales_staff_id": "TEXT REFERENCES sales_staff(id)"},
            "notification_plans": {"zalo_enabled": "INTEGER NOT NULL DEFAULT 0"},
            "notification_jobs": {
                "max_attempts": "INTEGER NOT NULL DEFAULT 3",
                "last_attempt_at": "TEXT",
                "provider_name": "TEXT",
                "provider_status": "TEXT",
                "is_mock": "INTEGER NOT NULL DEFAULT 1 CHECK(is_mock IN (0,1))",
                "provider_response_json": "TEXT",
            },
            "otp_challenges": {"consumed_at": "TEXT"},
            "idempotency_records": {
                "request_hash": "TEXT",
                "status": "TEXT NOT NULL DEFAULT 'succeeded'",
                "resource_id": "TEXT",
                "error_code": "TEXT",
                "expires_at": "TEXT",
            },
        }
        for table, columns in additions.items():
            existing = self._columns(connection, table)
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _split_statements(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    index = 0
    while index < len(script):
        char = script[index]
        if char == "'":
            in_string = not in_string
        if char == ";" and not in_string:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        index += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements

