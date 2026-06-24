from dataclasses import dataclass
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

    @property
    def duration_hours(self) -> float:
        """Długość slotu w godzinach z parametru czas_rezerwacji (liczba półgodzin)."""
        qs = parse_qs(urlparse(self.url).query)
        return int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5


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
