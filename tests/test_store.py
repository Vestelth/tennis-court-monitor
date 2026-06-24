import pytest

from store import Store


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "state.db")
    yield s
    s.close()


def test_disabled_by_default(store):
    assert store.enabled is False


def test_enable_then_disable(store):
    store.set_enabled(True)
    assert store.enabled is True
    store.set_enabled(False)
    assert store.enabled is False


def test_enabled_persists_across_reopen(tmp_path):
    path = tmp_path / "state.db"
    s1 = Store(path)
    s1.set_enabled(True)
    s1.close()

    s2 = Store(path)
    assert s2.enabled is True
    s2.close()


def test_slot_not_reported_initially(store):
    assert store.is_reported("Spojnia_24/06") is False


def test_mark_reported(store):
    store.mark_reported("Spojnia_24/06")
    assert store.is_reported("Spojnia_24/06") is True


def test_prune_removes_keys_no_longer_visible(store):
    store.mark_reported("Spojnia_24/06")
    store.mark_reported("Spojnia_25/06")
    store.prune_reported({"Spojnia_25/06"})
    assert store.is_reported("Spojnia_24/06") is False
    assert store.is_reported("Spojnia_25/06") is True


def test_reported_keys_returns_all_marked(store):
    store.mark_reported("A_24/06")
    store.mark_reported("B_25/06")
    assert store.reported_keys() == {"A_24/06", "B_25/06"}


def test_slot_scope_defaults_and_set(store):
    assert store.slot_scope == (0, 23)
    store.set_slot_scope(15, 21)
    assert store.slot_scope == (15, 21)


def test_monitor_hours_defaults_and_set(store):
    assert store.monitor_hours == (0, 23)
    store.set_monitor_hours(16, 22)
    assert store.monitor_hours == (16, 22)
