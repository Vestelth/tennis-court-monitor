"""Parser grafiku tenisowego ganadorsport.pl.

Inny układ niż kluby.org: grid divów, nie tabela. Każdy kort to para
`div.i-table-h-event-caption` (np. "KORT1 TRAWA") + wiersz `div.i-table-h-event-row`
z kafelkami `div.i-table-h-event-body` — zielone = wolne, czerwone = zajęte.
`data-start` to minuty od północy; sloty godzinowe. Datę bierzemy z `data-link` (t=).

Parsujemy widoczny grid (stabilny), nie przypadkowy debug-dump print_r na stronie.
"""

import re

from bs4 import BeautifulSoup

from models import Slot


def parse_ganador(html: str, surface: str) -> list[Slot]:
    """Wolne sloty dla kortów danej powierzchni ("TRAWA" / "MĄCZKA")."""
    soup = BeautifulSoup(html, "html.parser")

    captions = soup.select("div.i-table-h-event-caption")
    rows = soup.select("div.i-table-h-event-row")

    slots: list[Slot] = []
    want = surface.upper()

    for caption, row in zip(captions, rows):
        label = caption.get_text(strip=True).upper()
        if want not in label:
            continue

        for cell in row.select("div.i-table-h-event-body.green"):
            time_range = _time_range(cell.get("data-start"))
            date = _date_from_link(cell.get("data-link", ""))
            if time_range and date:
                slots.append(Slot(date=date, time_range=time_range))

    return slots


def _time_range(data_start) -> str | None:
    """Minuty od północy -> godzinowy zakres "HH:MM-HH:MM"."""
    if data_start is None:
        return None
    start = int(data_start)
    end = start + 60
    return f"{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}"


def _date_from_link(link: str) -> str | None:
    """Z data-link (...t=YYYY-MM-DD) zwraca "DD/MM" — spójnie z kluby.org."""
    m = re.search(r"t=(\d{4})-(\d{2})-(\d{2})", link)
    if not m:
        return None
    return f"{m.group(3)}/{m.group(2)}"
