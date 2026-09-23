import re
from dataclasses import dataclass, replace
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class Court:
    """Monitorowany kort (jeden typ obiektu na kluby.org).

    name: etykieta w powiadomieniach
    link: adres strony rezerwacji dla człowieka
    url:  endpoint AJAX grafiku (zawiera m.in. czas_rezerwacji)
    """

    name: str
    link: str
    url: str
    type: str = "kluby"  # "kluby" | "ganador"
    surface: str | None = None  # tylko ganador: "TRAWA" | "MĄCZKA"
    half_hours: int | None = None  # szukana długość gry; None = z czas_rezerwacji w url

    @property
    def duration_hours(self) -> float:
        """Długość slotu w godzinach (czas_rezerwacji to liczba półgodzin)."""
        if self.half_hours is not None:
            return self.half_hours * 0.5
        qs = parse_qs(urlparse(self.url).query)
        return int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5

    def with_duration(self, half_hours: int) -> "Court":
        """Wariant kortu dla danej długości gry (podmienia czas_rezerwacji, jeśli jest w adresach)."""

        def sub(u: str) -> str:
            return re.sub(r"czas_rezerwacji=\d+", f"czas_rezerwacji={half_hours}", u)

        return replace(self, url=sub(self.url), link=sub(self.link), half_hours=half_hours)


@dataclass(frozen=True)
class Slot:
    """Pojedynczy wolny slot na grafiku kortu.

    date:       dzień w formacie "DD/MM" (jak w nagłówku grafiku kluby.org)
    time_range: zakres godzin "HH:MM-HH:MM"
    """

    date: str
    time_range: str

    @property
    def start_hour(self) -> int:
        return int(self.time_range.split("-")[0].split(":")[0])

    @property
    def duration_hours(self) -> float:
        start, end = (_minutes(t) for t in self.time_range.split("-"))
        return (end - start) / 60


def _minutes(hhmm: str) -> int:
    h, m = hhmm.strip().split(":")
    return int(h) * 60 + int(m)
