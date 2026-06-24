from service import should_scan

HOURS = (16, 22)


def _kwargs(**over):
    base = dict(
        force=False,
        enabled=True,
        hour=18,
        hours=HOURS,
        now=1000.0,
        last_scan=0.0,
        interval=600,
    )
    base.update(over)
    return base


def test_force_always_scans_even_if_disabled():
    assert should_scan(**_kwargs(force=True, enabled=False, hour=3)) is True


def test_disabled_does_not_scan():
    assert should_scan(**_kwargs(enabled=False)) is False


def test_out_of_hours_does_not_scan():
    assert should_scan(**_kwargs(hour=9)) is False


def test_interval_not_elapsed_does_not_scan():
    assert should_scan(**_kwargs(now=500.0, last_scan=100.0, interval=600)) is False


def test_enabled_in_hours_and_interval_elapsed_scans():
    assert should_scan(**_kwargs(now=1000.0, last_scan=100.0, interval=600)) is True
