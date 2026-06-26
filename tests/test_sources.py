from pathlib import Path

import pytest

from models import Court
from sources import build_url, fetch_html, parse_slots

KLUBY_FIXTURE = Path(__file__).parent / "fixtures" / "spojnia_grafik.html"
GANADOR_FIXTURE = Path(__file__).parent / "fixtures" / "ganador_tenis.html"


class FakeResponse:
    def __init__(self, status_code=200, text="<html>ok</html>"):
        self.status_code = status_code
        self.text = text


def _kluby():
    return Court(name="Spojnia", link="l", url="https://kluby.org/ajax.php?klub=86&czas_rezerwacji=4")


def _ganador():
    return Court(
        name="Ganador – trawa",
        link="l",
        url="https://ganadorsport.pl/rezerwacja-online/index.php?s=grafik_zajec_tenis",
        type="ganador",
        surface="TRAWA",
    )


def test_build_url_kluby_uses_data_grafiku():
    assert "data_grafiku=2026-06-26" in build_url(_kluby(), "2026-06-26")


def test_build_url_ganador_uses_date():
    url = build_url(_ganador(), "2026-06-26")
    assert "date=2026-06-26" in url
    assert "data_grafiku" not in url


def test_fetch_html_returns_text_on_200():
    captured = []

    def getter(url, **kwargs):
        captured.append(url)
        return FakeResponse(text="<grafik/>")

    assert fetch_html(_kluby(), "2026-06-26", getter=getter) == "<grafik/>"


def test_fetch_html_returns_none_on_error_status():
    assert fetch_html(_kluby(), "2026-06-26", getter=lambda u, **k: FakeResponse(status_code=500)) is None


def test_fetch_html_returns_none_on_exception():
    def getter(url, **kwargs):
        raise ConnectionError("down")

    assert fetch_html(_kluby(), "2026-06-26", getter=getter) is None


def test_parse_slots_dispatches_kluby():
    html = KLUBY_FIXTURE.read_text(encoding="utf-8")
    assert len(parse_slots(_kluby(), html)) == 50


def test_parse_slots_dispatches_ganador_by_surface():
    html = GANADOR_FIXTURE.read_text(encoding="utf-8")
    assert len(parse_slots(_ganador(), html)) == 23
