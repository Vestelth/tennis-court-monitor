from pathlib import Path

import pytest

from ganador import parse_ganador
from models import Slot

FIXTURE = Path(__file__).parent / "fixtures" / "ganador_tenis.html"


@pytest.fixture
def html():
    return FIXTURE.read_text(encoding="utf-8")


def test_trawa_free_slot_count(html):
    # korty 1-4 (TRAWA): 23 wolne w zamrożonym fixture (26/06)
    assert len(parse_ganador(html, "TRAWA")) == 23


def test_maczka_free_slot_count(html):
    # korty 5-6 (MĄCZKA): 12 wolnych
    assert len(parse_ganador(html, "MĄCZKA")) == 12


def test_surface_filter_is_disjoint(html):
    trawa = parse_ganador(html, "TRAWA")
    maczka = parse_ganador(html, "MĄCZKA")
    assert len(trawa) + len(maczka) == 35  # wszystkie zielone


def test_contains_known_trawa_slot(html):
    # data-start 1020 = 17:00 -> slot godzinowy 17:00-18:00, dzień 26/06
    assert Slot(date="26/06", time_range="17:00-18:00") in parse_ganador(html, "TRAWA")


def test_slots_have_dd_mm_date_and_hourly_range(html):
    import re

    for slot in parse_ganador(html, "TRAWA"):
        assert re.fullmatch(r"\d{2}/\d{2}", slot.date)
        assert re.fullmatch(r"\d{2}:\d{2}-\d{2}:\d{2}", slot.time_range)


def test_empty_html_returns_no_slots():
    assert parse_ganador("", "TRAWA") == []
