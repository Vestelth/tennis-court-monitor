import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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


# ---------- spójność prawdziwego config.json (literówki = kort po cichu nieskanowany) ----------
REAL_CONFIG = Path(__file__).parent.parent / "config.json"


def _kluby_courts():
    return [c for c in load_courts(REAL_CONFIG) if c.type == "kluby"]


def _qs(url):
    return parse_qs(urlparse(url).query)


def test_real_config_link_points_to_same_object_type_as_data_url():
    for court in _kluby_courts():
        link_typ = _qs(court.link).get("typ_obiektu")
        if link_typ:  # niektóre linki (np. OSiR) nie mają typu
            assert link_typ == _qs(court.url)["typ_obiektu"], court.name


def test_real_config_kluby_uses_standard_schedule_endpoint():
    # wariant ..._termin.php odpowiada "Nie możesz rezerwować wstecz" -> 0 slotów
    for court in _kluby_courts():
        assert urlparse(court.url).path.endswith("/dostepne_korty_wybrany_typ.php"), court.name


def test_real_config_link_slug_is_unique_per_club():
    # ten sam slug strony (np. /umacieja/) nie może wskazywać na dwa różne kluby
    slug_to_klub = {}
    for court in _kluby_courts():
        slug = urlparse(court.link).path.split("/")[1]
        klub = _qs(court.url)["klub"][0]
        assert slug_to_klub.setdefault(slug, klub) == klub, f"{court.name}: /{slug}/ już przypisany do klub={slug_to_klub[slug]}"
