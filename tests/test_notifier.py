from models import Court, Slot
from notifier import TelegramNotifier, format_slot_message


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


def test_send_uses_timeout_so_dead_connection_cannot_hang_service():
    calls = []
    notifier = TelegramNotifier(
        "TOKEN", "123", poster=lambda url, **kw: calls.append((url, kw))
    )

    notifier.send("hej")

    url, kw = calls[0]
    assert url.endswith("/botTOKEN/sendMessage")
    assert kw["json"] == {"chat_id": "123", "text": "hej"}
    assert kw["timeout"] > 0


def test_message_uses_slot_duration_not_court_default():
    court = Court(name="S", link="https://l?czas_rezerwacji=3", url="https://x?czas_rezerwacji=4")
    msg = format_slot_message(court, Slot(date="24/06", time_range="06:00-07:30"))
    assert "1.5h" in msg
