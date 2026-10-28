"""NEFF meat probe (BLE) integration."""

from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import LEGACY_TITLE
from .coordinator import NeffProbeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

type NeffProbeConfigEntry = ConfigEntry[NeffProbeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NeffProbeConfigEntry) -> bool:
    """Set up a probe from a config entry."""
    address = entry.data[CONF_ADDRESS]
    coordinator = NeffProbeCoordinator(hass, address)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_cancel_expiry)
    entry.async_on_unload(coordinator.async_start())
    entry.async_on_unload(
        bluetooth.async_register_advertisement_callback(
            hass, coordinator.async_handle_advertisement, address
        )
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NeffProbeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: NeffProbeConfigEntry) -> bool:
    """Migrate entries created by version 0.1.x."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        title = "NEFF Meat Probe" if entry.title == LEGACY_TITLE else entry.title
        hass.config_entries.async_update_entry(entry, title=title, minor_version=2)
        _LOGGER.debug("Migrated %s to version 1.2", entry.entry_id)
    return True
