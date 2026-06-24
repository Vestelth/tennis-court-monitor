"""Wczytanie statycznej konfiguracji kortów z pliku JSON.

Ustawienia zmieniane w runtime (zakres godzin, godziny monitoringu, włączenie)
nie należą tu — trzyma je store (SQLite). Tu jest tylko lista monitorowanych kortów.
"""

import json
from pathlib import Path

from models import Court


def load_courts(path: str | Path) -> list[Court]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Court(name=item["name"], link=item["link"], url=item["url"])
        for item in data["urls"]
    ]
