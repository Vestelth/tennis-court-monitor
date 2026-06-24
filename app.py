"""Spinka jednego przebiegu skanu (bez pętli/harmonogramu — to Etap 3).

scan_once dla każdego kortu: pobiera grafik, parsuje wolne sloty, wybiera te
warte powiadomienia (zakres godzin, pierwszy na dzień, niezgłoszone), wysyła
powiadomienia, zapisuje je jako zgłoszone i sprząta klucze, których już nie ma.
"""

from typing import Callable, Iterable

from models import Court
from monitor import notifiable_slots, slot_key, visible_keys
from notifier import format_slot_message
from scraper import fetch_grid, parse_free_slots


def scan_once(
    courts: Iterable[Court],
    store,
    notifier,
    today: str,
    fetch: Callable[[Court, str], "str | None"] = fetch_grid,
) -> int:
    """Wykonuje jeden przebieg skanu. Zwraca liczbę wysłanych powiadomień."""
    scope = store.slot_scope
    visible: set[str] = set()
    notified = 0

    for court in courts:
        html = fetch(court, today)
        if html is None:
            continue

        slots = parse_free_slots(html)
        visible |= visible_keys(court.name, slots, scope)

        for slot in notifiable_slots(court.name, slots, scope, store.reported_keys()):
            notifier.send(format_slot_message(court, slot))
            store.mark_reported(slot_key(court.name, slot))
            notified += 1

    store.prune_reported(visible)
    return notified
