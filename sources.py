"""Abstrakcja źródła grafików — spina różne platformy pod jednym interfejsem.

Każdy kort ma `type` ("kluby" | "ganador"). Tu wiemy, jak dla danego typu:
- zbudować URL grafiku na konkretny dzień (`build_url`),
- pobrać HTML z obsługą błędów sieci (`fetch_html`),
- sparsować HTML do listy slotów właściwym parserem (`parse_slots`).

Dzięki temu `app`/`service` nie wiedzą, z jakiej strony pochodzą dane.
"""

from typing import Callable, Optional

import requests

from ganador import parse_ganador
from models import Court, Slot
from scraper import parse_free_slots

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

# nazwa parametru daty w URL grafiku, per platforma
_DATE_PARAM = {"kluby": "data_grafiku", "ganador": "date"}


def build_url(court: Court, date: str) -> str:
    param = _DATE_PARAM.get(court.type, "data_grafiku")
    sep = "&" if "?" in court.url else "?"
    return f"{court.url}{sep}{param}={date}"


def fetch_html(
    court: Court,
    date: str,
    getter: Callable[..., object] = requests.get,
) -> Optional[str]:
    """Pobiera HTML grafiku na dany dzień; None przy błędzie sieci lub statusie != 200."""
    try:
        response = getter(build_url(court, date), headers=_HEADERS, timeout=30)
    except (requests.RequestException, OSError):
        return None
    if response.status_code != 200:
        return None
    return response.text


def parse_slots(court: Court, html: str) -> list[Slot]:
    if court.type == "ganador":
        return parse_ganador(html, court.surface or "")
    return parse_free_slots(html)
