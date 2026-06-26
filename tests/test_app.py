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


def test_transient_failure_does_not_cause_renotification(store):
    # Dwa korty z tym samym grafikiem; B chwilowo nie odpowiada w przebiegu 2.
    court_a = Court(name="A", link="la", url="https://a?czas_rezerwacji=4")
    court_b = Court(name="B", link="lb", url="https://b?czas_rezerwacji=4")
    courts = [court_a, court_b]
    html = FIXTURE.read_text(encoding="utf-8")

    def fetch_factory(failing):
        return lambda c, t: None if c.name in failing else html

    # przebieg 1: oba OK -> zgłaszają sloty
    n1 = FakeNotifier()
    scan_once(courts, store, n1, today="2026-06-24", fetch=fetch_factory(set()))
    assert len(n1.sent) == 16  # 8 dni x 2 korty

    # przebieg 2: B pada -> nie wolno wyczyścić zgłoszeń B
    n2 = FakeNotifier()
    scan_once(courts, store, n2, today="2026-06-24", fetch=fetch_factory({"B"}))
    assert n2.sent == []

    # przebieg 3: B znów OK -> sloty B nadal zgłoszone, brak ponownych powiadomień
    n3 = FakeNotifier()
    scan_once(courts, store, n3, today="2026-06-24", fetch=fetch_factory(set()))
    assert n3.sent == []
