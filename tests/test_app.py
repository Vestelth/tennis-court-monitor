from pathlib import Path

import pytest

from app import scan_once
from models import Court
from store import Store

FIXTURE = Path(__file__).parent / "fixtures" / "spojnia_grafik.html"


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "state.db")
    yield s
    s.close()


def _court():
    return Court(name="Spojnia", link="https://kluby.org/spojnia", url="https://x?czas_rezerwacji=4")


def _fixture_fetch(court, today):
    return FIXTURE.read_text(encoding="utf-8")


def test_scan_notifies_first_slot_per_date(store):
    # domyślny zakres (0,23) — fixture ma sloty w 8 dniach
    notifier = FakeNotifier()
    scan_once([_court()], store, notifier, today="2026-06-24", fetch=_fixture_fetch)
    assert len(notifier.sent) == 8


def test_scan_does_not_renotify_on_second_run(store):
    notifier = FakeNotifier()
    scan_once([_court()], store, notifier, today="2026-06-24", fetch=_fixture_fetch)
    scan_once([_court()], store, notifier, today="2026-06-24", fetch=_fixture_fetch)
    assert len(notifier.sent) == 8  # drugi przebieg nie dorzuca nic


def test_scan_respects_scope(store):
    store.set_slot_scope(15, 21)
    notifier = FakeNotifier()
    scan_once([_court()], store, notifier, today="2026-06-24", fetch=_fixture_fetch)
    # mniej dni niż przy pełnym zakresie, ale > 0
    assert 0 < len(notifier.sent) < 8


def test_scan_skips_court_when_fetch_fails(store):
    notifier = FakeNotifier()
    scan_once([_court()], store, notifier, today="2026-06-24", fetch=lambda c, t: None)
    assert notifier.sent == []
