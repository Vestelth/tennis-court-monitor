from models import Court, Slot
from notifier import TelegramNotifier, format_grouped_messages


def _k(name, link="https://kluby.org/x?czas_rezerwacji=4"):
    return Court(name=name, link=link, url="https://x?czas_rezerwacji=4")


def test_grouped_message_groups_slots_by_court_with_all_fields():
    spojnia, bemowo = _k("Spojnia Gorna"), _k("OSiR Bemowo", "https://kluby.org/b?czas_rezerwacji=3")
    items = [
        (spojnia, Slot(date="24/06", time_range="15:00-17:00")),
        (bemowo, Slot(date="24/06", time_range="18:00-19:30")),
        (spojnia, Slot(date="25/06", time_range="16:00-18:00")),
    ]

    [msg] = format_grouped_messages(items)

    assert "3" in msg.splitlines()[0]  # nagłówek z liczbą slotów
    assert msg.count("Spojnia Gorna") == 1 and msg.count("OSiR Bemowo") == 1
    spojnia_block = msg[msg.index("Spojnia Gorna") : msg.index("OSiR Bemowo")]
    assert "24/06 15:00-17:00 (2h)" in spojnia_block
    assert "25/06 16:00-18:00 (2h)" in spojnia_block
    assert "https://kluby.org/x?czas_rezerwacji=4" in spojnia_block
    assert "24/06 18:00-19:30 (1.5h)" in msg
    assert "https://kluby.org/b?czas_rezerwacji=3" in msg


def test_grouped_message_sorts_dates_and_lists_each_distinct_link_once():
    k4, k3 = _k("S"), _k("S", "https://kluby.org/x?czas_rezerwacji=3")
    items = [
        (k4, Slot(date="26/06", time_range="15:00-17:00")),
        (k3, Slot(date="24/06", time_range="10:00-11:30")),
        (k4, Slot(date="25/06", time_range="15:00-17:00")),
    ]
    [msg] = format_grouped_messages(items)
    assert msg.index("24/06") < msg.index("25/06") < msg.index("26/06")
    assert msg.count("czas_rezerwacji=4") == 1 and msg.count("czas_rezerwacji=3") == 1


def test_grouped_message_sorts_across_new_year():
    k = _k("S")
    items = [(k, Slot(date="02/01", time_range="15:00-17:00")), (k, Slot(date="30/12", time_range="15:00-17:00"))]
    [msg] = format_grouped_messages(items)
    assert msg.index("30/12") < msg.index("02/01")


def test_grouped_messages_split_under_telegram_limit_without_breaking_court_block():
    items = [
        (_k(f"Kort {i:02d}"), Slot(date=f"{d:02d}/06", time_range="15:00-17:00"))
        for i in range(30)
        for d in range(1, 8)
    ]
    msgs = format_grouped_messages(items, limit=1000)
    assert len(msgs) > 1
    assert all(len(m) <= 1000 for m in msgs)
    joined = "\n".join(msgs)
    for i in range(30):
        assert joined.count(f"Kort {i:02d}\n") == 1  # każdy blok kortu w całości, raz
    assert sum(m.count("\n• ") for m in msgs) == 210


def test_no_items_no_messages():
    assert format_grouped_messages([]) == []


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
