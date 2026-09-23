"""Parser grafiku tenisowego ganadorsport.pl.

Inny układ niż kluby.org: grid divów, nie tabela. Każdy kort to para
`div.i-table-h-event-caption` (np. "KORT1 TRAWA") + wiersz `div.i-table-h-event-row`
z kafelkami `div.i-table-h-event-body` — zielone = wolne, czerwone = zajęte.
`data-start` to minuty od północy; sloty godzinowe. Datę bierzemy z `data-link` (t=).

Parsujemy widoczny grid (stabilny), nie przypadkowy debug-dump print_r na stronie.
"""

import math
import re

from bs4 import BeautifulSoup

from models import Slot


def parse_ganador(html: str, surface: str, hours: float = 1) -> list[Slot]:
    """Wolne sloty dla kortów danej powierzchni ("TRAWA" / "MĄCZKA").

    Kafelki są godzinowe, więc długość gry `hours` zaokrąglamy w górę do pełnych
    godzin i szukamy tylu kolejnych wolnych kafelków na tym samym korcie.
    """
    soup = BeautifulSoup(html, "html.parser")

    captions = soup.select("div.i-table-h-event-caption")
    rows = soup.select("div.i-table-h-event-row")

    slots: list[Slot] = []
    want = surface.upper()
    need = max(1, math.ceil(hours))

    for caption, row in zip(captions, rows):
        label = caption.get_text(strip=True).upper()
        if want not in label:
            continue

        cells = row.select("div.i-table-h-event-body")
        for i in range(len(cells) - need + 1):
            window = cells[i : i + need]
            if not all(_is_free(c) for c in window):
                continue
            starts = [int(c.get("data-start")) for c in window]
            if starts != list(range(starts[0], starts[0] + 60 * need, 60)):
                continue  # dziura w grafiku — to nie są kolejne godziny
            date = _date_from_link(window[0].get("data-link", ""))
            if date:
                slots.append(Slot(date=date, time_range=_time_range(starts[0], 60 * need)))

    return slots


def _is_free(cell) -> bool:
    return "green" in (cell.get("class") or []) and cell.get("data-start") is not None


def _time_range(start: int, minutes: int) -> str:
    """Minuty od północy + długość -> zakres "HH:MM-HH:MM"."""
    end = start + minutes
    return f"{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}"


def _date_from_link(link: str) -> str | None:
    """Z data-link (...t=YYYY-MM-DD) zwraca "DD/MM" — spójnie z kluby.org."""
    m = re.search(r"t=(\d{4})-(\d{2})-(\d{2})", link)
    if not m:
        return None
    return f"{m.group(3)}/{m.group(2)}"
