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


def _slots_html(times):
    """Minimalny grafik kluby.org: jeden dzień 24/06, sloty o podanych zakresach."""
    rows = "".join(
        f'<tr><td>x</td><td><a class="btn-success"><span>{t}</span></a></td></tr>' for t in times
    )
    return f'<table><thead><tr><th>h</th><th class="text-center">Śr 24/06</th></tr></thead><tbody>{rows}</tbody></table>'


def _court_with_link():
    return Court(name="Spojnia", link="https://kluby.org/spojnia?czas_rezerwacji=4", url="https://x?czas_rezerwacji=4")


def test_duration_range_prefers_longest_available(store):
    store.set_duration_range(3, 4)
    html_by_czas = {"3": _slots_html(["10:00-11:30"]), "4": _slots_html(["18:00-20:00"])}
    fetched = []

    def fetch(court, today):
        fetched.append(court.url)
        return html_by_czas[court.url.split("czas_rezerwacji=")[1]]

    notifier = FakeNotifier()
    scan_once([_court_with_link()], store, notifier, today="2026-06-24", fetch=fetch)

    assert len(fetched) == 2  # 1.5h i 2h
    assert len(notifier.sent) == 1  # jeden na dzień
    assert "18:00-20:00" in notifier.sent[0] and "2.0h" in notifier.sent[0]
    assert "czas_rezerwacji=4" in notifier.sent[0]


def test_duration_range_falls_back_to_shorter(store):
    store.set_duration_range(3, 4)
    html_by_czas = {"3": _slots_html(["10:00-11:30"]), "4": _slots_html([])}
    notifier = FakeNotifier()
    scan_once(
        [_court_with_link()], store, notifier, today="2026-06-24",
        fetch=lambda c, t: html_by_czas[c.url.split("czas_rezerwacji=")[1]],
    )
    assert len(notifier.sent) == 1
    assert "10:00-11:30" in notifier.sent[0] and "1.5h" in notifier.sent[0]
    assert "czas_rezerwacji=3" in notifier.sent[0]


def test_court_skipped_when_any_duration_fetch_fails(store):
    store.set_duration_range(3, 4)
    notifier = FakeNotifier()
    scan_once(
        [_court()], store, notifier, today="2026-06-24",
        fetch=lambda c, t: None if "czas_rezerwacji=4" in c.url else _slots_html(["10:00-11:30"]),
    )
    assert notifier.sent == []


def test_ganador_fetched_once_for_duration_range(store):
    store.set_duration_range(3, 4)
    court = Court(name="G", link="https://g", url="https://g", type="ganador", surface="TRAWA")
    calls = []
    html = (Path(__file__).parent / "fixtures" / "ganador_tenis.html").read_text(encoding="utf-8")
    scan_once([court], store, FakeNotifier(), today="2026-06-24",
              fetch=lambda c, t: calls.append((c.url, t)) or html)
    assert len(calls) == 7  # raz na dzień, mimo dwóch długości gry
    assert len(set(calls)) == 7


def test_ganador_scans_seven_days_once_each(store):
    store.set_duration_range(3, 4)
    court = Court(name="G", link="https://g", url="https://g", type="ganador", surface="MĄCZKA")
    html = (Path(__file__).parent / "fixtures" / "ganador_tenis.html").read_text(encoding="utf-8")
    days = []
    scan_once([court], store, FakeNotifier(), today="2026-09-27",
              fetch=lambda c, t: days.append(t) or html)
    assert days == ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30",
                    "2026-10-01", "2026-10-02", "2026-10-03"]


def test_ganador_court_skipped_when_one_day_fails(store):
    court = Court(name="G", link="https://g", url="https://g", type="ganador", surface="MĄCZKA")
    html = (Path(__file__).parent / "fixtures" / "ganador_tenis.html").read_text(encoding="utf-8")
    notifier = FakeNotifier()
    scan_once([court], store, notifier, today="2026-09-27",
              fetch=lambda c, t: None if t == "2026-09-30" else html)
    assert notifier.sent == []
