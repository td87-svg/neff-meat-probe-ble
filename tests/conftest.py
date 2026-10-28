"""Fixtures for the NEFF meat probe tests."""

from __future__ import annotations

import time

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from habluetooth import BluetoothServiceInfoBleak, get_manager
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.neff_probe_ble.const import DOMAIN

ADDRESS = "FC:25:3F:00:00:01"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


@pytest.fixture(autouse=True)
def bluetooth(enable_bluetooth: None) -> None:
    """Set up a mocked Bluetooth stack in all tests."""


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NEFF Meat Probe",
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS},
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


def probe_service_info(
    payload_hex: str = "1817171717001801060808a60200",
    rssi: int = -60,
    address: str = ADDRESS,
    name: str = "BSHwfth",
) -> BluetoothServiceInfoBleak:
    """Build service info for a probe packet (payload incl. 2 ID bytes)."""
    payload = bytes.fromhex(payload_hex) if payload_hex else b""
    manufacturer_data = (
        {int.from_bytes(payload[:2], "little"): payload[2:]} if payload else {}
    )
    raw = bytes([len(name) + 1, 0x09]) + name.encode()
    if payload:
        raw = bytes([len(payload) + 1, 0xFF]) + payload + raw
    adv = AdvertisementData(
        local_name=name,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=rssi,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=rssi,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[],
        source="local",
        device=BLEDevice(address, name, None),
        advertisement=adv,
        connectable=False,
        time=time.monotonic(),
        tx_power=None,
        raw=raw,
    )


def inject_bluetooth_service_info(
    hass: HomeAssistant, info: BluetoothServiceInfoBleak
) -> None:
    """Feed a packet into Home Assistant's Bluetooth manager."""
    get_manager().scanner_adv_received(info)
