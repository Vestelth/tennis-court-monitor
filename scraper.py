"""Klient i parser grafiku dostępności kortów kluby.org.

Parser jest czysty: dostaje HTML grafiku jednego typu obiektu i zwraca listę
wszystkich wolnych slotów. Filtrowanie po zakresie godzin i deduplikację
zostawiamy warstwie wyżej (app/store) — tu chodzi tylko o wierne odczytanie grafiku.
"""

from bs4 import BeautifulSoup

from models import Slot


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
