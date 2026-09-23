from models import Court, Slot


def test_slot_start_hour_from_time_range():
    assert Slot(date="25/06", time_range="06:00-08:00").start_hour == 6


def test_slot_start_hour_evening():
    assert Slot(date="01/07", time_range="22:00-00:00").start_hour == 22


def test_slot_duration_hours_from_time_range():
    assert Slot(date="24/06", time_range="06:00-07:30").duration_hours == 1.5
    assert Slot(date="24/06", time_range="18:00-20:00").duration_hours == 2.0


def test_with_duration_replaces_czas_rezerwacji_in_url_and_link():
    court = Court(
        name="S",
        link="https://kluby.org/s/dostepnosc?typ_obiektu=188&czas_rezerwacji=4",
        url="https://kluby.org/ajax.php?klub=86&czas_rezerwacji=4&typ_obiektu=188",
    )
    c3 = court.with_duration(3)
    assert "czas_rezerwacji=3" in c3.url and "czas_rezerwacji=4" not in c3.url
    assert "czas_rezerwacji=3" in c3.link
    assert "klub=86" in c3.url and "typ_obiektu=188" in c3.url
    assert c3.duration_hours == 1.5


def test_with_duration_keeps_ganador_urls_but_sets_duration():
    court = Court(name="G", link="https://g/x", url="https://g/x", type="ganador", surface="TRAWA")
    c3 = court.with_duration(3)
    assert c3.url == "https://g/x" and c3.link == "https://g/x"
    assert c3.duration_hours == 1.5
