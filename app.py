"""Spinka jednego przebiegu skanu (bez pętli/harmonogramu — to Etap 3).

scan_once dla każdego kortu: pobiera grafik, parsuje wolne sloty, wybiera te
warte powiadomienia (zakres godzin, pierwszy na dzień, niezgłoszone). Na końcu
wysyła JEDNĄ zbiorczą wiadomość (lub kilka, gdy długa), dopiero potem zapisuje sloty
jako zgłoszone — błąd wysyłki = nic nie zapisane, następny skan ponowi. Sprząta
klucze slotów, których już nie ma.
"""

from typing import Callable, Iterable

from models import Court, Slot
from monitor import notifiable_slots, slot_key, visible_keys
from notifier import format_grouped_messages
from sources import fetch_html, parse_slots, schedule_dates


def scan_once(
    courts: Iterable[Court],
    store,
    notifier,
    today: str,
    fetch: Callable[[Court, str], "str | None"] = fetch_html,
) -> int:
    """Wykonuje jeden przebieg skanu. Zwraca liczbę wysłanych powiadomień."""
    scope = store.slot_scope
    low, high = store.duration_range
    visible: set[str] = set()
    scanned_names: list[str] = []
    new: list[tuple[Court, Slot]] = []

    for court in courts:
        slots = _slots_for_durations(court, today, range(high, low - 1, -1), fetch)
        if slots is None:
            # kort nie odpowiedział — nie ruszamy jego zgłoszeń (inaczej re-notyfikacja)
            continue
        scanned_names.append(court.name)

        visible |= visible_keys(court.name, slots, scope)

        for slot in notifiable_slots(court.name, slots, scope, store.reported_keys()):
            new.append((court.with_duration(round(slot.duration_hours * 2)), slot))

    for message in format_grouped_messages(new):
        notifier.send(message)
    for court, slot in new:
        store.mark_reported(slot_key(court.name, slot))

    # sprzątamy zniknięte sloty TYLKO dla kortów pobranych w tym przebiegu
    candidates = {
        key
        for key in store.reported_keys()
        if any(key.startswith(f"{name}_") for name in scanned_names)
    }
    store.discard_reported(candidates - visible)
    return len(new)


def _slots_for_durations(court, today, durations, fetch):
    """Wolne sloty kortu dla każdej długości gry (od najdłuższej); None, gdy któryś fetch padł.

    Kolejność ma znaczenie: monitor bierze pierwszy slot na dzień, więc wygrywa
    najdłuższa dostępna gra. Ten sam adres i dzień (Ganador) pobieramy tylko raz.
    Brak choćby jednego dnia = kort pomijany w całości (inaczej re-notyfikacja).
    """
    html_cache: dict[tuple[str, str], "str | None"] = {}
    slots = []
    for half_hours in durations:
        variant = court.with_duration(half_hours)
        for day in schedule_dates(court, today):
            key = (variant.url, day)
            if key not in html_cache:
                html_cache[key] = fetch(variant, day)
            html = html_cache[key]
            if html is None:
                return None
            slots += parse_slots(variant, html)
    return slots
