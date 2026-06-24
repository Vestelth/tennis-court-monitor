"""Czysta logika decyzyjna skanera (bez I/O).

Z listy wszystkich wolnych slotów jednego kortu wybiera te, o których warto
powiadomić: w zadanym zakresie godzin, po jednym na dzień, z pominięciem już
zgłoszonych. Odtwarza zachowanie v1, ale jako testowalne funkcje czyste.
"""

from models import Slot


def slot_key(court_name: str, slot: Slot) -> str:
    """Klucz deduplikacji powiadomień: jeden na (kort, dzień)."""
    return f"{court_name}_{slot.date}"


def _in_scope(slot: Slot, scope: tuple[int, int]) -> bool:
    start, end = scope
    return start <= slot.start_hour <= end


def visible_keys(court_name: str, slots: list[Slot], scope: tuple[int, int]) -> set[str]:
    """Klucze wszystkich dni, które mają teraz wolny slot w zakresie godzin."""
    return {slot_key(court_name, s) for s in slots if _in_scope(s, scope)}


def notifiable_slots(
    court_name: str,
    slots: list[Slot],
    scope: tuple[int, int],
    reported: set[str],
) -> list[Slot]:
    """Sloty do powiadomienia: w zakresie, pierwszy na dzień, jeszcze niezgłoszone."""
    result: list[Slot] = []
    seen_dates: set[str] = set()
    for slot in slots:
        if not _in_scope(slot, scope):
            continue
        if slot.date in seen_dates:
            continue
        seen_dates.add(slot.date)
        if slot_key(court_name, slot) in reported:
            continue
        result.append(slot)
    return result
