"""Trwały stan skanera w SQLite.

Zastępuje pliki-flagi v1 (enabled.txt, force_run.txt) i state.json:
- włączenie monitoringu,
- zakres godzin slotów i godziny działania monitoringu,
- zbiór już zgłoszonych slotów (deduplikacja powiadomień).
"""

import sqlite3
from pathlib import Path

_DEFAULTS = {
    "enabled": "0",
    "scope_start": "0",
    "scope_end": "23",
    "hours_start": "0",
    "hours_end": "23",
    "last_update_id": "0",
}


class Store:
    def __init__(self, db_path: str | Path):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS reported (key TEXT PRIMARY KEY)"
        )
        for key, value in _DEFAULTS.items():
            self._conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        self._conn.commit()

    # ---------- ustawienia ----------

    def _get(self, key: str) -> str:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0]

    def _set(self, key: str, value: str) -> None:
        self._conn.execute(
            "UPDATE settings SET value = ? WHERE key = ?", (value, key)
        )
        self._conn.commit()

    @property
    def enabled(self) -> bool:
        return self._get("enabled") == "1"

    def set_enabled(self, value: bool) -> None:
        self._set("enabled", "1" if value else "0")

    @property
    def slot_scope(self) -> tuple[int, int]:
        return int(self._get("scope_start")), int(self._get("scope_end"))

    def set_slot_scope(self, start: int, end: int) -> None:
        self._set("scope_start", str(start))
        self._set("scope_end", str(end))

    @property
    def monitor_hours(self) -> tuple[int, int]:
        return int(self._get("hours_start")), int(self._get("hours_end"))

    def set_monitor_hours(self, start: int, end: int) -> None:
        self._set("hours_start", str(start))
        self._set("hours_end", str(end))

    @property
    def last_update_id(self) -> int:
        return int(self._get("last_update_id"))

    def set_last_update_id(self, value: int) -> None:
        self._set("last_update_id", str(value))

    # ---------- zgłoszone sloty ----------

    def is_reported(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM reported WHERE key = ?", (key,)
        ).fetchone()
        return row is not None

    def mark_reported(self, key: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO reported (key) VALUES (?)", (key,)
        )
        self._conn.commit()

    def reported_keys(self) -> set[str]:
        return {row[0] for row in self._conn.execute("SELECT key FROM reported")}

    def discard_reported(self, keys: set[str]) -> None:
        """Usuwa wskazane klucze ze zgłoszonych (np. sloty, które zniknęły)."""
        self._conn.executemany(
            "DELETE FROM reported WHERE key = ?", ((k,) for k in keys)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
