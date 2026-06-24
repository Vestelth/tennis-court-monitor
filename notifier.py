"""Powiadomienia Telegram.

format_slot_message jest czyste (testowalne). TelegramNotifier wysyła wiadomość
przez Bot API; poster wstrzykiwany dla testowalności (domyślnie requests.post).
"""

from typing import Callable

import requests

from models import Court, Slot


def format_slot_message(court: Court, slot: Slot) -> str:
    return (
        f"Wolny kort: {court.name}\n"
        f"Data: {slot.date}\n"
        f"Termin: {slot.time_range}\n"
        f"Długość: {court.duration_hours}h\n"
        f"{court.link}"
    )


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
        self._poster(self._url, json={"chat_id": self._chat_id, "text": text})
