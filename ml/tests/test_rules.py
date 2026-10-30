from datetime import datetime, timedelta, timezone

import pytest

from ml.rules import crosswind, od_state_machine, r18_usable, tailwind

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def winds(minutes, direction=70, speed=5):
    return [(T + timedelta(minutes=m), direction, speed, speed) for m in minutes]


def test_brief_examples():
    assert tailwind(20, 30, 180) == pytest.approx(17.3205, abs=0.001)
    assert tailwind(20, 45, 180) == pytest.approx(14.1421, abs=0.001)
    assert od_state_machine(winds([0], 90, 20)) == ["07"]
    assert r18_usable(20, 330) is False
    assert r18_usable(20, 45) is True


def test_boundaries_and_gust_crosswind():
    assert r18_usable(15, 0) is False
    assert r18_usable(14.99, 0) is True
    assert r18_usable(10, 90, 40) is True
    assert r18_usable(10, 90, 40.01) is False
    assert crosswind(20, 90, 180) == pytest.approx(20)
    assert od_state_machine(winds([0], 70, 10)) == ["07"]


def test_hysteresis_and_reset():
    assert od_state_machine(winds([0, 20, 30, 40])) == ["25", "25", "25", "07"]
    rows = winds([0]) + winds([20], None) + winds([40, 60, 80])
    assert od_state_machine(rows) == ["25", "25", "25", "25", "07"]
    assert od_state_machine(winds([0, 60], 250)) == ["25", "25"]
    assert od_state_machine(winds([0, 60], None, 0)) == ["25", "25"]


def test_invalid_order_and_unknown_usability():
    with pytest.raises(ValueError):
        od_state_machine(winds([10, 0]))
    assert r18_usable(10, None) is None
    assert r18_usable(0, None) is True
