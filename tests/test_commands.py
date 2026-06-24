import pytest

from commands import handle_command
from models import Court
from store import Store

COURTS = [
    Court(name="Spojnia Gorna", link="x", url="https://x?czas_rezerwacji=4"),
    Court(name="OSiR Bemowo", link="y", url="https://y?czas_rezerwacji=4"),
]


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "state.db")
    yield s
    s.close()


def test_start_enables_monitoring(store):
    reply = handle_command("/start", store, COURTS)
    assert store.enabled is True
    assert "łączony" in reply or "wlaczony" in reply.lower()


def test_stop_disables_monitoring(store):
    store.set_enabled(True)
    reply = handle_command("/stop", store, COURTS)
    assert store.enabled is False
    assert reply  # jakaś odpowiedź potwierdzająca


def test_hours_sets_monitor_hours(store):
    handle_command("/hours 16 22", store, COURTS)
    assert store.monitor_hours == (16, 22)


def test_scope_sets_slot_scope(store):
    handle_command("/scope 15 21", store, COURTS)
    assert store.slot_scope == (15, 21)


def test_hours_with_bad_args_returns_usage_and_does_not_change(store):
    reply = handle_command("/hours 16", store, COURTS)
    assert store.monitor_hours == (0, 23)  # bez zmian
    assert "ż" in reply.lower() or "uzy" in reply.lower()  # "Użycie:"


def test_list_returns_court_names(store):
    reply = handle_command("/list", store, COURTS)
    assert "Spojnia Gorna" in reply
    assert "OSiR Bemowo" in reply


def test_status_includes_state_and_settings(store):
    store.set_enabled(True)
    store.set_monitor_hours(16, 22)
    store.set_slot_scope(15, 21)
    reply = handle_command("/status", store, COURTS)
    assert "16-22" in reply
    assert "15-21" in reply
    assert "2" in reply  # liczba kortów


def test_help_lists_commands(store):
    reply = handle_command("/help", store, COURTS)
    for cmd in ("/start", "/stop", "/status", "/list", "/hours", "/scope"):
        assert cmd in reply


def test_unknown_command_returns_none(store):
    assert handle_command("cześć", store, COURTS) is None
