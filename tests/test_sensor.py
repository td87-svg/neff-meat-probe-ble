"""Tests for setup, sensors, availability and diagnostics."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ADDRESS, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.neff_probe_ble.const import DOMAIN, LEGACY_TITLE, STALE_SECONDS
from custom_components.neff_probe_ble.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import ADDRESS, inject_bluetooth_service_info, probe_service_info

MEAN = "sensor.neff_meat_probe_average"
CHANNEL_1 = "sensor.neff_meat_probe_channel_1"
LAST = "sensor.neff_meat_probe_last_valid_packet"


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> MockConfigEntry:
    """Set up the integration with all entities enabled."""
    for key in ("channel_1", "channel_2", "channel_3", "channel_4", "rssi"):
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{ADDRESS}_{key}",
            config_entry=config_entry,
            suggested_object_id=f"neff_meat_probe_{key}",
        )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_unavailable_until_first_packet(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Without packets (probe docked) all entities are unavailable."""
    assert setup_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(MEAN).state == STATE_UNAVAILABLE
    assert hass.states.get(CHANNEL_1).state == STATE_UNAVAILABLE
    assert hass.states.get(LAST).state == STATE_UNAVAILABLE


async def test_values(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    """A valid packet updates all sensors."""
    inject_bluetooth_service_info(
        hass, probe_service_info("1e2020201b00210b060808a60200")
    )
    await hass.async_block_till_done()

    mean = hass.states.get(MEAN)
    assert float(mean.state) == 31.5
    assert mean.attributes["unit_of_measurement"] == "°C"
    assert mean.attributes["decoder_status"] == "reverse_engineered"
    assert mean.attributes["candidate_channels"] == [30, 32, 32, 32]
    assert mean.attributes["raw_byte4"] == 0x1B
    assert hass.states.get(CHANNEL_1).state == "30"
    assert hass.states.get("sensor.neff_meat_probe_channel_4").state == "32"
    assert hass.states.get("sensor.neff_meat_probe_rssi").state == "-60"
    assert hass.states.get(LAST).state != STATE_UNAVAILABLE


async def test_expires_when_probe_goes_silent(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Temperatures become unavailable; the last packet time stays visible."""
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    assert float(hass.states.get(MEAN).state) == 23.25
    last = hass.states.get(LAST).state

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=STALE_SECONDS + 1)
    )
    await hass.async_block_till_done()

    assert hass.states.get(MEAN).state == STATE_UNAVAILABLE
    assert hass.states.get(CHANNEL_1).state == STATE_UNAVAILABLE
    assert hass.states.get(LAST).state == last

    # The next packet revives the sensors.
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    assert float(hass.states.get(MEAN).state) == 23.25


async def test_identical_packets_keep_sensor_fresh(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """A probe at a constant temperature repeats the same payload."""
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=200))
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=200))
    await hass.async_block_till_done()
    assert float(hass.states.get(MEAN).state) == 23.25


async def test_ignores_cached_and_name_only_packets(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Cached repeats (RSSI -127) and scan responses do not change values."""
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    inject_bluetooth_service_info(
        hass, probe_service_info("1e2020201b00210b060808a60200", rssi=-127)
    )
    inject_bluetooth_service_info(hass, probe_service_info(payload_hex=""))
    await hass.async_block_till_done()
    assert float(hass.states.get(MEAN).state) == 23.25


async def test_unknown_payload_makes_unavailable_without_error_log(
    hass: HomeAssistant, setup_entry: MockConfigEntry, caplog: pytest.LogCaptureFixture
) -> None:
    """An undecodable packet hides old values but logs no error."""
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    inject_bluetooth_service_info(
        hass, probe_service_info("6565656565011801060808a60200")
    )
    await hass.async_block_till_done()
    assert hass.states.get(MEAN).state == STATE_UNAVAILABLE
    assert not [r for r in caplog.records if r.levelname in ("WARNING", "ERROR")]
    # The rejected payload is kept for analysis (diagnostics, debug log).
    assert "payload 6565656565011801060808a60200" in caplog.text
    diag = await async_get_config_entry_diagnostics(hass, setup_entry)
    assert diag["last_rejected_head_hex"] == "656565656501180106"


async def test_diagnostics_redact_address(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Diagnostics contain values but not the Bluetooth address."""
    inject_bluetooth_service_info(hass, probe_service_info())
    await hass.async_block_till_done()
    diag = await async_get_config_entry_diagnostics(hass, setup_entry)
    assert diag["channels"] == [24, 23, 23, 23]
    assert diag["available"] is True
    assert diag["payload_head_hex"] == "181717171700180106"
    assert ADDRESS not in str(diag)
    assert ADDRESS.lower() not in str(diag)


async def test_unload(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    """The entry unloads cleanly."""
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.NOT_LOADED


async def test_migrate_legacy_entry_keeps_entity_ids(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Entries from 0.1.x keep their entity IDs and get a new title."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=LEGACY_TITLE,
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS},
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    legacy_id = (
        "sensor.neff_bratenthermometer_ble_experimentell_mittelwert_experimentell"
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{ADDRESS}_mean",
        config_entry=entry,
        suggested_object_id=legacy_id.removeprefix("sensor."),
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.title == "NEFF Meat Probe"
    assert entry.minor_version == 2
    assert hass.states.get(legacy_id) is not None
    assert hass.states.get(MEAN) is None
