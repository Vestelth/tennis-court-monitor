"""Obsługa komend Telegram — czysta logika nad store.

handle_command dostaje tekst wiadomości, mutuje store i zwraca odpowiedź tekstową
(albo None, gdy to nie jest znana komenda). Wysyłka i odpytywanie Telegrama są poza
tym modułem (service.py) — dzięki temu cała logika komend jest testowalna bez sieci.
"""

from models import Court
from store import Store

_HELP = (
    "Dostępne komendy:\n\n"
    "/start – włącza monitoring\n"
    "/stop – wyłącza monitoring\n"
    "/status – pokazuje ustawienia\n"
    "/list – lista monitorowanych kortów\n"
    "/hours H1 H2 – godziny działania monitoringu\n"
    "/scope H1 H2 – zakres godzin slotów\n"
    "/run – wymusza natychmiastowy skan\n"
    "/help – pokazuje tę pomoc"
)


def handle_command(text: str, store: Store, courts: list[Court]) -> str | None:
    text = text.strip()

    if text == "/start":
        store.set_enabled(True)
        return "Monitoring włączony"

    if text == "/stop":
        store.set_enabled(False)
        return "Monitoring zatrzymany"

    if text == "/help":
        return _HELP

    if text == "/list":
        lines = ["Monitorowane korty:"]
        lines += [f"- {c.name}" for c in courts]
        return "\n".join(lines)

    if text == "/status":
        h1, h2 = store.monitor_hours
        s1, s2 = store.slot_scope
        return (
            "Status monitoringu:\n"
            f"Aktywny: {'TAK' if store.enabled else 'NIE'}\n"
            f"Godziny działania: {h1}-{h2}\n"
            f"Zakres godzin slotów: {s1}-{s2}\n"
            f"Liczba kortów: {len(courts)}"
        )

    if text.startswith("/hours"):
        return _set_range(text, store.set_monitor_hours, "godziny działania monitoringu")

    if text.startswith("/scope"):
        return _set_range(text, store.set_slot_scope, "zakres godzin slotów")

    return None


def _set_range(text: str, setter, label: str) -> str:
    parts = text.split()
    if len(parts) < 3:
        return f"Użycie: {parts[0]} 16 22"
    try:
        start, end = int(parts[1]), int(parts[2])
    except ValueError:
        return f"Użycie: {parts[0]} 16 22"
    setter(start, end)
    return f"Ustawiono {label}: {start}-{end}"
