"""Sensors for the NEFF meat probe."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_ADDRESS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NeffProbeConfigEntry
from .const import DECODER_STATUS, DOMAIN
from .coordinator import NeffProbeCoordinator


@dataclass(frozen=True, kw_only=True)
class NeffProbeSensorDescription(SensorEntityDescription):
    """Describe a probe sensor."""

    value_fn: Callable[[NeffProbeCoordinator], float | int | datetime | None]


def _channel(index: int) -> NeffProbeSensorDescription:
    return NeffProbeSensorDescription(
        key=f"channel_{index + 1}",
        translation_key="channel",
        translation_placeholders={"channel": str(index + 1)},
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.sample.channels[index] if c.sample else None,
    )


SENSORS: tuple[NeffProbeSensorDescription, ...] = (
    NeffProbeSensorDescription(
        key="mean",
        translation_key="mean",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda c: c.sample.mean if c.sample else None,
    ),
    *(_channel(index) for index in range(4)),
    NeffProbeSensorDescription(
        key="ambient",
        translation_key="ambient",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda c: c.sample.ambient if c.sample else None,
    ),
    NeffProbeSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.rssi,
    ),
    NeffProbeSensorDescription(
        key="last_received",
        translation_key="last_received",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.received_at,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NeffProbeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the probe sensors."""
    async_add_entities(
        NeffProbeSensor(entry.runtime_data, entry, description)
        for description in SENSORS
    )


class NeffProbeSensor(
    PassiveBluetoothCoordinatorEntity[NeffProbeCoordinator], SensorEntity
):
    """A probe value; unavailable instead of stale when no packets arrive."""

    _attr_has_entity_name = True
    entity_description: NeffProbeSensorDescription

    def __init__(
        self,
        coordinator: NeffProbeCoordinator,
        entry: NeffProbeConfigEntry,
        description: NeffProbeSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        address = entry.data[CONF_ADDRESS]
        # Unique IDs are unchanged since 0.1.0 so existing entity IDs survive.
        self._attr_unique_id = f"{address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            name="NEFF Meat Probe",
            manufacturer="NEFF",
            model="Z1365WX0",
        )

    @property
    def available(self) -> bool:
        """Keep the time of the last packet visible while the probe is silent."""
        if self.entity_description.key == "last_received":
            return self.coordinator.received_at is not None
        return super().available

    @property
    def native_value(self) -> float | int | datetime | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the raw payload on the mean sensor for further analysis."""
        sample = self.coordinator.sample
        if self.entity_description.key != "mean" or sample is None:
            return None
        return {
            "decoder_status": DECODER_STATUS,
            "candidate_channels": list(sample.channels),
            "candidate_rounded_mean": sample.rounded_mean,
            "full_manufacturer_hex": sample.raw.hex(),
            "raw_byte4": sample.raw[4],
            "raw_byte6": sample.raw[6],
            "last_valid_packet": (
                self.coordinator.received_at.isoformat()
                if self.coordinator.received_at
                else None
            ),
            "source": self.coordinator.source,
        }
