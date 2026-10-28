"""Tests for the battery level estimate."""

from __future__ import annotations

import pytest

from custom_components.neff_probe_ble.battery import (
    WINDOW,
    BatteryEstimator,
    reading_to_percent,
)
from custom_components.neff_probe_ble.decoder import decode_advertisement


@pytest.mark.parametrize(
    ("reading", "percent"),
    [
        (1600, 100),
        (1544, 100),
        (1514, 70),
        (1468, 50),
        (1449, 30),
        (1434.5, 15),  # extrapolated below the lowest calibration point
        (1420, 0),
        (1300, 0),
    ],
)
def test_reading_to_percent(reading: float, percent: int) -> None:
    """The calibration table is interpolated and clamped."""
    assert reading_to_percent(reading) == pytest.approx(percent)


def test_reading_from_packet() -> None:
    """Offsets 7-8 are read as uint16 little endian."""
    payload = bytes.fromhex("1313131414001408060808a60200")
    sample = decode_advertisement({}, bytes([len(payload) + 1, 0xFF]) + payload)
    assert sample.battery_reading == 1544


def test_noise_does_not_flicker() -> None:
    """Noise of ±4 around a reading keeps one 5 % step."""
    estimator = BatteryEstimator()
    levels = {estimator.update(reading) for reading in [1514, 1518, 1510] * 10}
    assert estimator.level == 70
    assert levels <= {65, 70, 75}
    # After settling, the noise no longer changes the level.
    assert {estimator.update(r) for r in [1518, 1510, 1517, 1511] * 10} == {70}


def test_heat_does_not_raise_level() -> None:
    """A hot probe reads higher; the level must not rise while sending."""
    estimator = BatteryEstimator()
    for _ in range(WINDOW):
        estimator.update(1514)
    for _ in range(3 * WINDOW):
        estimator.update(1540)
    assert estimator.level == 70


def test_discharge_in_steps() -> None:
    """A falling reading lowers the level in 5 % steps."""
    estimator = BatteryEstimator()
    seen = []
    for reading in range(1544, 1440, -1):
        for _ in range(WINDOW):
            level = estimator.update(reading)
            if not seen or seen[-1] != level:
                seen.append(level)
    assert seen == sorted(seen, reverse=True)
    assert all(level % 5 == 0 for level in seen)
    assert seen[0] == 100
    assert seen[-1] in (20, 25)


def test_reset_after_charging() -> None:
    """After a pause (docked) the level may rise again."""
    estimator = BatteryEstimator()
    for _ in range(WINDOW):
        estimator.update(1449)
    assert estimator.level == 30
    estimator.reset()
    assert estimator.level is None
    for _ in range(WINDOW):
        estimator.update(1544)
    assert estimator.level == 100
