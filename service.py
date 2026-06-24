"""Długożyjąca usługa skanera (Etap 3).

Jeden proces: long-polling komend Telegram (natychmiastowe odpowiedzi) + skan
grafików co `SCAN_INTERVAL`, jeśli monitoring włączony i mieści się w godzinach
działania. Stan w SQLite (store). Uruchamiany pod systemd na Mikrusie (Etap 4).

Wymagane zmienne środowiskowe: BOT_TOKEN, CHAT_ID.
"""

import datetime
import os
import time
from pathlib import Path

import requests

from app import scan_once
from commands import handle_command
from config import load_courts
from notifier import TelegramNotifier
from store import Store

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
DB_PATH = BASE_DIR / "state.db"
SCAN_INTERVAL = 600  # sekundy między skanami (10 min)
POLL_TIMEOUT = 30  # long-polling getUpdates


def should_scan(
    *,
    force: bool,
    enabled: bool,
    hour: int,
    hours: tuple[int, int],
    now: float,
    last_scan: float,
    interval: float,
) -> bool:
    """Czy wykonać skan w tym obrocie pętli."""
    if force:
        return True
    if not enabled:
        return False
    start, end = hours
    if not (start <= hour <= end):
        return False
    return (now - last_scan) >= interval


def _get_updates(token: str, offset: int) -> list[dict]:
    response = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={"offset": offset, "timeout": POLL_TIMEOUT},
        timeout=POLL_TIMEOUT + 10,
    )
    return response.json().get("result", [])


def run() -> None:  # pragma: no cover - pętla sieciowa, weryfikowana przy deployu
    token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    courts = load_courts(CONFIG_PATH)
    store = Store(DB_PATH)
    notifier = TelegramNotifier(token, chat_id)

    last_scan = 0.0
    while True:
        force = False

        for update in _get_updates(token, store.last_update_id + 1):
            store.set_last_update_id(max(store.last_update_id, update["update_id"]))
            text = (update.get("message") or {}).get("text", "")
            if text == "/run":
                notifier.send("Wymuszam natychmiastowy skan…")
                force = True
                continue
            reply = handle_command(text, store, courts)
            if reply:
                notifier.send(reply)

        now = time.time()
        if should_scan(
            force=force,
            enabled=store.enabled,
            hour=datetime.datetime.now().hour,
            hours=store.monitor_hours,
            now=now,
            last_scan=last_scan,
            interval=SCAN_INTERVAL,
        ):
            today = datetime.date.today().strftime("%Y-%m-%d")
            scan_once(courts, store, notifier, today)
            last_scan = now


if __name__ == "__main__":  # pragma: no cover
    run()
