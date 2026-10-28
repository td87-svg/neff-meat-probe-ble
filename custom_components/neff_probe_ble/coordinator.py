"""Receive probe advertisements through Home Assistant's Bluetooth stack.

The probe is never connected to or paired. While it sits in its charger it
often sends nothing, so the absence of packets is normal and only makes the
measurements unavailable; it is never logged as an error.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import math
from time import monotonic

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .battery import BatteryEstimator
from .const import STALE_SECONDS
from .decoder import (
    NoManufacturerData,
    ProbeSample,
    decode_advertisement,
    manufacturer_payload,
)

_LOGGER = logging.getLogger(__name__)

# Some adapters re-deliver the last cached packet with this placeholder RSSI.
CACHED_RSSI = -127


class NeffProbeCoordinator(PassiveBluetoothDataUpdateCoordinator):
    """Keep the latest valid sample and expire it after STALE_SECONDS."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            address,
            # Active scanning is needed to receive the local name.
            bluetooth.BluetoothScanningMode.ACTIVE,
            connectable=False,
        )
        self.sample: ProbeSample | None = None
        self.sample_time = -1.0
        self.received_at: datetime | None = None
        self.rssi: int | None = None
        self.source: str | None = None
        self.last_error: str | None = None
        self.last_rejected: bytes | None = None
        self.battery = BatteryEstimator()
        self._cancel_expiry: Callable[[], None] | None = None

    @property
    def available(self) -> bool:
        """Return True while a fresh valid sample exists."""
        return super().available and self.sample is not None

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Validate a packet and store it if it is newer than the last one."""
        if (
            service_info.address.upper() != self.address.upper()
            or service_info.rssi == CACHED_RSSI
        ):
            return
        packet_time = float(service_info.time)
        now = monotonic()
        if not math.isfinite(packet_time) or packet_time > now + 1:
            return
        # A replayed cached packet must not revive or replace a newer reading.
        if packet_time <= self.sample_time or now - packet_time >= STALE_SECONDS:
            return
        try:
            sample = decode_advertisement(
                service_info.manufacturer_data, getattr(service_info, "raw", None)
            )
        except NoManufacturerData:
            # A name-only scan response neither refreshes nor invalidates.
            return
        except (ValueError, TypeError, OverflowError) as err:
            payload = manufacturer_payload(
                service_info.manufacturer_data, getattr(service_info, "raw", None)
            )
            _LOGGER.debug(
                "Ignoring undecodable packet from %s: %s (payload %s, rssi %s)",
                self.address,
                err,
                payload.hex() if payload else None,
                service_info.rssi,
            )
            self.last_error = str(err)
            self.last_rejected = payload
            self._available = False
            self.async_update_listeners()
            return
        self.sample = sample
        self.sample_time = packet_time
        self.received_at = dt_util.utcnow() - timedelta(
            seconds=max(0, now - packet_time)
        )
        self.rssi = service_info.rssi
        self.source = service_info.source
        self.last_error = None
        self.battery.update(sample.battery_reading)
        self.async_cancel_expiry()
        self._cancel_expiry = async_call_later(
            self.hass, STALE_SECONDS - max(0, now - packet_time), self._async_expire
        )
        super()._async_handle_bluetooth_event(service_info, change)

    @callback
    def async_handle_advertisement(
        self, service_info: bluetooth.BluetoothServiceInfoBleak
    ) -> None:
        """Handle every received packet, including unchanged repeats.

        Home Assistant only reports changed advertisements to coordinators.
        A probe at a stable temperature repeats the same payload, which must
        still count as a fresh reading.
        """
        self._async_handle_bluetooth_event(
            service_info, bluetooth.BluetoothChange.ADVERTISEMENT
        )

    @callback
    def _async_expire(self, _now: datetime) -> None:
        """Mark measurements unavailable when no packet arrived in time."""
        self._cancel_expiry = None
        self._available = False
        # The probe was probably docked and charging: estimate afresh.
        self.battery.reset()
        self.async_update_listeners()

    @callback
    def async_cancel_expiry(self) -> None:
        """Cancel a pending expiry timer."""
        if self._cancel_expiry:
            self._cancel_expiry()
            self._cancel_expiry = None
