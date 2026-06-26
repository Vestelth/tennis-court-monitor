"""Klient i parser grafiku dostępności kortów kluby.org.

Parser jest czysty: dostaje HTML grafiku jednego typu obiektu i zwraca listę
wszystkich wolnych slotów. Filtrowanie po zakresie godzin i deduplikację
zostawiamy warstwie wyżej (app/store) — tu chodzi tylko o wierne odczytanie grafiku.
"""

from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup

from models import Court, Slot

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}


def fetch_grid(
    court: Court,
    date: str,
    getter: Callable[..., object] = requests.get,
) -> Optional[str]:
    """Pobiera HTML grafiku kortu na dany dzień ("YYYY-MM-DD").

    Zwraca tekst odpowiedzi albo None, gdy serwer nie odpowie 200.
    getter jest wstrzykiwany dla testowalności (domyślnie requests.get).
    """
    sep = "&" if "?" in court.url else "?"
    url = f"{court.url}{sep}data_grafiku={date}"
    try:
        response = getter(url, headers=_HEADERS, timeout=30)
    except (requests.RequestException, OSError):
        return None
    if response.status_code != 200:
        return None
    return response.text


def parse_free_slots(html: str) -> list[Slot]:
    """Wyciąga wszystkie wolne sloty (a.btn-success) z HTML grafiku.

    Kolumny tabeli odpowiadają kolejnym dniom z nagłówka (thead),
    więc indeks komórki mapujemy na datę z nagłówka.
    """
    soup = BeautifulSoup(html, "html.parser")

    dates = _parse_header_dates(soup)
    slots: list[Slot] = []

    for row in soup.select("tbody tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        # pierwsza komórka to kolumna godzin — pomijamy ją, resztę mapujemy na daty
        for idx, cell in enumerate(cells[1:]):
            anchor = cell.select_one("a.btn-success")
            if not anchor:
                continue

            span = anchor.find("span")
            if not span:
                continue
            time_range = span.get_text(strip=True)

            if idx >= len(dates):
                continue

            slots.append(Slot(date=dates[idx], time_range=time_range))

    return slots


def _parse_header_dates(soup: BeautifulSoup) -> list[str]:
    """Z nagłówka grafiku zwraca listę dat "DD/MM" w kolejności kolumn."""
    dates: list[str] = []
    for th in soup.select("thead th.text-center"):
        parts = th.get_text(separator=" ", strip=True).split()
        if len(parts) >= 2:
            dates.append(parts[-1])
    return dates
