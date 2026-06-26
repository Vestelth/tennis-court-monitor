import json
from pathlib import Path

import pytest

from config import load_courts
from models import Court

SAMPLE = {
    "urls": [
        {
            "name": "Spojnia Gorna",
            "link": "https://kluby.org/spojnia-gorna/dostepnosc?typ_obiektu=188&czas_rezerwacji=4",
            "url": "https://kluby.org/klub/ajax/dostepne_korty_wybrany_typ.php?klub=86&id_strony_klubu=60&czy_dedykowane=0&typ_obiektu=188&czas_rezerwacji=4",
        },
        {
            "name": "Morelowa - hard",
            "link": "https://kluby.org/mtc/dostepnosc?typ_obiektu=636&czas_rezerwacji=2",
            "url": "https://kluby.org/klub/ajax/dostepne_korty_wybrany_typ.php?klub=14&typ_obiektu=63&czas_rezerwacji=2",
        },
    ]
}


GANADOR_SAMPLE = {
    "urls": [
        {
            "name": "Ganador – trawa",
            "type": "ganador",
            "surface": "TRAWA",
            "link": "https://ganadorsport.pl/rezerwacja-online/index.php?s=grafik_zajec_tenis",
            "url": "https://ganadorsport.pl/rezerwacja-online/index.php?s=grafik_zajec_tenis",
        }
    ]
}


@pytest.fixture
def config_path(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return p


def test_load_courts_reads_type_and_surface(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(GANADOR_SAMPLE), encoding="utf-8")
    court = load_courts(p)[0]
    assert court.type == "ganador"
    assert court.surface == "TRAWA"


def test_load_courts_returns_all(config_path):
    courts = load_courts(config_path)
    assert [c.name for c in courts] == ["Spojnia Gorna", "Morelowa - hard"]


def test_court_keeps_link_and_url(config_path):
    court = load_courts(config_path)[0]
    assert court.link.startswith("https://kluby.org/spojnia-gorna")
    assert "dostepne_korty_wybrany_typ.php" in court.url


def test_court_duration_hours_from_czas_rezerwacji():
    # czas_rezerwacji to liczba półgodzin: 4 -> 2.0h, 2 -> 1.0h
    four = Court(name="a", link="x", url="https://x?czas_rezerwacji=4")
    two = Court(name="b", link="x", url="https://x?czas_rezerwacji=2")
    assert four.duration_hours == 2.0
    assert two.duration_hours == 1.0


def test_court_duration_defaults_when_missing():
    court = Court(name="a", link="x", url="https://x?typ_obiektu=1")
    assert court.duration_hours == 1.0


def test_court_defaults_to_kluby_type():
    court = Court(name="a", link="x", url="https://x")
    assert court.type == "kluby"
    assert court.surface is None
