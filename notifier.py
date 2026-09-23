"""Powiadomienia Telegram.

format_grouped_messages jest czyste (testowalne): wszystkie nowe sloty ze skanu
w jednej wiadomości, pogrupowane po kortach. TelegramNotifier wysyła wiadomość
przez Bot API; poster wstrzykiwany dla testowalności (domyślnie requests.post).
"""

from typing import Callable

import requests

from models import Court, Slot

# Bez timeoutu zerwane połączenie (np. zgubione pakiety IPv6) wiesza całą usługę.
SEND_TIMEOUT = 15  # sekundy


# limit Telegrama to 4096 znaków — zostawiamy zapas
MESSAGE_LIMIT = 4000


def format_grouped_messages(
    items: list[tuple[Court, Slot]], limit: int = MESSAGE_LIMIT
) -> list[str]:
    """Nowe sloty jako wiadomości zbiorcze: blok na kort, daty rosnąco.

    `court` przy slocie to wariant z linkiem dla jego długości gry — pod blokiem
    kortu wypisujemy każdy różny link raz. Gdy tekst przekroczy `limit`, dzielimy
    na kilka wiadomości, nigdy w środku bloku kortu.
    """
    if not items:
        return []

    by_court: dict[str, list[tuple[Court, Slot]]] = {}
    for court, slot in items:
        by_court.setdefault(court.name, []).append((court, slot))

    date_key = _date_sort_key({slot.date for _, slot in items})
    blocks = []
    for name, entries in by_court.items():
        entries.sort(key=lambda e: (date_key(e[1].date), e[1].time_range))
        lines = [name]
        lines += [
            f"• {slot.date} {slot.time_range} ({slot.duration_hours:g}h)" for _, slot in entries
        ]
        lines += list(dict.fromkeys(court.link for court, _ in entries))
        blocks.append("\n".join(lines))

    header = f"🎾 Nowe wolne korty: {len(items)}"
    messages, current = [], header
    for block in blocks:
        candidate = f"{current}\n\n{block}"
        if len(candidate) > limit and current != header:
            messages.append(current)
            candidate = f"{header} (cd.)\n\n{block}"
        current = candidate
    messages.append(current)
    return messages


def _date_sort_key(dates: set[str]):
    """Klucz sortowania "DD/MM"; przez przełom roku styczeń idzie po grudniu."""
    months = {int(d.split("/")[1]) for d in dates}
    wraps = 12 in months and 1 in months

    def key(d: str) -> tuple[int, int]:
        day, month = (int(x) for x in d.split("/"))
        if wraps and month < 7:
            month += 12
        return month, day

    return key


class TelegramNotifier:
    def __init__(
        self,
        token: str,
        chat_id: str,
        poster: Callable[..., object] = requests.post,
    ):
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._poster = poster

    def send(self, text: str) -> None:
        self._poster(
            self._url,
            json={"chat_id": self._chat_id, "text": text},
            timeout=SEND_TIMEOUT,
        )
