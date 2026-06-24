from models import Court, Slot
from notifier import format_slot_message


def test_format_slot_message_contains_all_fields():
    court = Court(
        name="Spojnia Gorna",
        link="https://kluby.org/spojnia/dostepnosc",
        url="https://x?czas_rezerwacji=4",
    )
    slot = Slot(date="24/06", time_range="15:00-17:00")

    msg = format_slot_message(court, slot)

    assert "Spojnia Gorna" in msg
    assert "24/06" in msg
    assert "15:00-17:00" in msg
    assert "2.0h" in msg  # czas_rezerwacji=4 -> 2.0h
    assert "https://kluby.org/spojnia/dostepnosc" in msg
