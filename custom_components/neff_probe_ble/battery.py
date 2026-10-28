"""Estimate the battery level from the probe's battery reading.

Offsets 7-8 (uint16 little endian) fall steadily while the probe discharges,
most likely the battery voltage. The table below was calibrated against the
Home Connect app at room temperature from 100 % down to 30 %. Lower levels are
extrapolated: a drained probe simply stops sending, so there is no packet that
marks "empty". This module has no Home Assistant dependency.
"""

from __future__ import annotations

from collections import deque
from itertools import pairwise
import math

# (reading, percent), ascending.
CALIBRATION: tuple[tuple[int, int], ...] = (
    (1420, 0),  # extrapolated
    (1449, 30),
    (1468, 50),
    (1486, 55),
    (1496, 60),
    (1514, 70),
    (1527, 80),
    (1544, 100),
)
STEP = 5
# Readings averaged against noise (about ±4, i.e. ±3 %).
WINDOW = 10
# Extra margin below a step boundary before the level drops.
HYSTERESIS = 1.5


def reading_to_percent(reading: float) -> float:
    """Interpolate the calibration table, clamped to 0-100 %."""
    if reading <= CALIBRATION[0][0]:
        return 0.0
    for (low_reading, low_pct), (high_reading, high_pct) in pairwise(CALIBRATION):
        if reading <= high_reading:
            share = (reading - low_reading) / (high_reading - low_reading)
            return low_pct + share * (high_pct - low_pct)
    return 100.0


def _round_to_step(percent: float) -> int:
    return min(100, max(0, math.floor(percent / STEP + 0.5) * STEP))


class BatteryEstimator:
    """Turn noisy readings into a level in 5 % steps, like the app.

    Heat raises the reading by roughly 15 % in a hot oven, and the battery
    does not charge while the probe is sending. So once the average has
    settled, the level only ever falls, with hysteresis at each step.
    Call reset() when the probe has been silent (docked) to start over.
    """

    def __init__(self) -> None:
        """Initialize the estimator."""
        self._readings: deque[int] = deque(maxlen=WINDOW)
        self.level: int | None = None

    def reset(self) -> None:
        """Forget the readings, e.g. after the probe was in its charger."""
        self._readings.clear()
        self.level = None

    def update(self, reading: int) -> int:
        """Add a reading and return the current level."""
        self._readings.append(reading)
        percent = reading_to_percent(sum(self._readings) / len(self._readings))
        if self.level is None or len(self._readings) < WINDOW:
            # Still settling: follow the average in both directions.
            self.level = _round_to_step(percent)
        elif percent < self.level - STEP / 2 - HYSTERESIS:
            self.level = min(self.level - STEP, _round_to_step(percent))
        return self.level
