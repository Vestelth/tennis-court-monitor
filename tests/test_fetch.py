from models import Court
from scraper import fetch_grid


class FakeResponse:
    def __init__(self, status_code=200, text="<html>ok</html>"):
        self.status_code = status_code
        self.text = text


def _court():
    return Court(
        name="Spojnia",
        link="https://kluby.org/spojnia/dostepnosc",
        url="https://kluby.org/klub/ajax/dostepne_korty_wybrany_typ.php?klub=86&czas_rezerwacji=4",
    )


def test_fetch_grid_appends_date_and_returns_text():
    calls = []

    def getter(url, **kwargs):
        calls.append(url)
        return FakeResponse(text="<grafik/>")

    html = fetch_grid(_court(), "2026-06-24", getter=getter)

    assert html == "<grafik/>"
    assert "data_grafiku=2026-06-24" in calls[0]


def test_fetch_grid_returns_none_on_error_status():
    def getter(url, **kwargs):
        return FakeResponse(status_code=503, text="boom")

    assert fetch_grid(_court(), "2026-06-24", getter=getter) is None


def test_fetch_grid_returns_none_on_request_exception():
    def getter(url, **kwargs):
        raise ConnectionError("network down")

    assert fetch_grid(_court(), "2026-06-24", getter=getter) is None
