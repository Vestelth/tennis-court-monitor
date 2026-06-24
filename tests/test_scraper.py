import re
from collections import Counter
from pathlib import Path

import pytest

from models import Slot
from scraper import parse_free_slots

FIXTURE = Path(__file__).parent / "fixtures" / "spojnia_grafik.html"

# Ground truth wyprowadzony z fixture spojnia_grafik.html (grafik 24/06–01/07),
# zachowanie referencyjne v1: każdy <a class="btn-success"> = jeden wolny slot.
EXPECTED_TOTAL = 50
EXPECTED_PER_DATE = {
    "24/06": 5,
    "25/06": 16,
    "26/06": 6,
    "27/06": 3,
    "28/06": 8,
    "29/06": 8,
    "30/06": 2,
    "01/07": 2,
}


@pytest.fixture
def html():
    return FIXTURE.read_text(encoding="utf-8")


def test_total_free_slots(html):
    assert len(parse_free_slots(html)) == EXPECTED_TOTAL


def test_free_slots_per_date(html):
    counts = Counter(slot.date for slot in parse_free_slots(html))
    assert dict(counts) == EXPECTED_PER_DATE


def test_contains_known_slot(html):
    assert Slot(date="25/06", time_range="06:00-08:00") in parse_free_slots(html)


def test_all_slots_have_valid_shape(html):
    slots = parse_free_slots(html)
    for slot in slots:
        assert slot.date in EXPECTED_PER_DATE
        assert re.fullmatch(r"\d{2}:\d{2}-\d{2}:\d{2}", slot.time_range)


def test_empty_html_returns_no_slots():
    assert parse_free_slots("") == []
