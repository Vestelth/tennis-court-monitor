from models import Slot
from monitor import notifiable_slots, slot_key, visible_keys


def _slots(*pairs):
    return [Slot(date=d, time_range=t) for d, t in pairs]


def test_slot_key_combines_court_and_date():
    assert slot_key("Spojnia", Slot(date="24/06", time_range="15:00-17:00")) == "Spojnia_24/06"


def test_visible_keys_only_includes_in_scope():
    slots = _slots(("24/06", "06:00-08:00"), ("24/06", "16:00-18:00"), ("25/06", "23:00-01:00"))
    assert visible_keys("X", slots, scope=(15, 21)) == {"X_24/06"}


def test_notifiable_keeps_first_in_scope_slot_per_date():
    slots = _slots(("24/06", "16:00-18:00"), ("24/06", "17:00-19:00"), ("25/06", "15:00-17:00"))
    result = notifiable_slots("X", slots, scope=(15, 21), reported=set())
    assert result == _slots(("24/06", "16:00-18:00"), ("25/06", "15:00-17:00"))


def test_notifiable_excludes_out_of_scope():
    slots = _slots(("24/06", "06:00-08:00"), ("24/06", "22:00-00:00"))
    assert notifiable_slots("X", slots, scope=(15, 21), reported=set()) == []


def test_notifiable_excludes_already_reported():
    slots = _slots(("24/06", "16:00-18:00"), ("25/06", "15:00-17:00"))
    result = notifiable_slots("X", slots, scope=(15, 21), reported={"X_24/06"})
    assert result == _slots(("25/06", "15:00-17:00"))
