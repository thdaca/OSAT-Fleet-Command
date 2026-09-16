"""Step 11A: the small indexed SQLite maintenance-ticket branch."""

from __future__ import annotations

from contextlib import contextmanager
import json
import sqlite3
import threading
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = ("OPEN", "ACKNOWLEDGED", "IN_PROGRESS")


class MaintenanceRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.revision = 0
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS maintenance_ticket (
                    ticket_id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ticket_machine_status "
                "ON maintenance_ticket(machine_id, status, updated_utc)"
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.row_factory = sqlite3.Row
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _json(payload: Mapping[str, Any]) -> str:
        return json.dumps(dict(payload), ensure_ascii=False, sort_keys=True)

    def save(self, payload: Mapping[str, Any]) -> None:
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO maintenance_ticket (
                    ticket_id, machine_id, status, priority,
                    created_utc, updated_utc, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["ticket_id"],
                    payload["machine_id"],
                    payload["status"],
                    payload["priority"],
                    payload["created_utc"],
                    payload["updated_utc"],
                    self._json(payload),
                ),
            )
        self.revision += 1

    def update(self, payload: Mapping[str, Any]) -> None:
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE maintenance_ticket
                SET status=?, priority=?, updated_utc=?, payload_json=?
                WHERE ticket_id=?
                """,
                (
                    payload["status"],
                    payload["priority"],
                    payload["updated_utc"],
                    self._json(payload),
                    payload["ticket_id"],
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(str(payload["ticket_id"]))
        self.revision += 1

    def active_for_machine(self, machine_id: str) -> dict[str, Any] | None:
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM maintenance_ticket "
                f"WHERE machine_id=? AND status IN ({placeholders}) "
                "ORDER BY updated_utc DESC LIMIT 1",
                (machine_id, *ACTIVE_STATUSES),
            ).fetchone()
        return None if row is None else json.loads(row["payload_json"])

    def list_tickets(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM maintenance_ticket "
                "ORDER BY updated_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def prior_context(self, machine_id: str, *, limit: int = 5) -> tuple[str, ...]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM maintenance_ticket "
                "WHERE machine_id=? ORDER BY updated_utc DESC LIMIT ?",
                (machine_id, limit),
            ).fetchall()
        context: list[str] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            context.append(
                " | ".join(
                    str(payload.get(name, ""))
                    for name in ("health_state", "summary", "likely_issue")
                    if payload.get(name)
                )
            )
        return tuple(item for item in context if item)
