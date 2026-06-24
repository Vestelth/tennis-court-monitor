from models import Slot


def test_slot_start_hour_from_time_range():
    assert Slot(date="25/06", time_range="06:00-08:00").start_hour == 6


def test_slot_start_hour_evening():
    assert Slot(date="01/07", time_range="22:00-00:00").start_hour == 22
