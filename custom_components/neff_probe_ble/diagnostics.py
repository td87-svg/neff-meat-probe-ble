"""Diagnostics for the NEFF meat probe."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from . import NeffProbeConfigEntry
from .const import DECODER_STATUS
from .decoder import PAYLOAD_LENGTH

TO_REDACT = {CONF_ADDRESS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: NeffProbeConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    sample = coordinator.sample
    return {
        # entry.as_dict() would leak the address through discovery_keys.
        "entry": {
            "title": entry.title,
            "version": f"{entry.version}.{entry.minor_version}",
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "decoder_status": DECODER_STATUS,
        "available": coordinator.available,
        "last_valid_packet": (
            coordinator.received_at.isoformat() if coordinator.received_at else None
        ),
        "last_error": coordinator.last_error,
        "rssi": coordinator.rssi,
        "channels": list(sample.channels) if sample else None,
        "mean": sample.mean if sample else None,
        # Bytes 0-8 change with temperature. The constant tail might identify
        # the individual probe, so it is left out.
        "payload_head_hex": sample.raw[:9].hex() if sample else None,
        "last_rejected_head_hex": (
            coordinator.last_rejected[:9].hex() if coordinator.last_rejected else None
        ),
        "payload_length": PAYLOAD_LENGTH,
    }
