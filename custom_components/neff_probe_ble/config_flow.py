"""Config flow for the NEFF meat probe."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
import probatio

from .const import DOMAIN, LOCAL_NAME

TITLE = "NEFF Meat Probe"
MAC_PATTERN = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}")


class NeffProbeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up one probe per Bluetooth address."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize the flow."""
        self._address: str | None = None
        self._discovered: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a probe found by Bluetooth discovery."""
        if discovery_info.name != LOCAL_NAME:
            return self.async_abort(reason="not_supported")
        self._address = discovery_info.address.upper()
        await self.async_set_unique_id(self._address)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"address": self._address}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered probe."""
        assert self._address is not None
        if user_input is not None:
            return self.async_create_entry(
                title=TITLE, data={CONF_ADDRESS: self._address}
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"address": self._address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a discovered probe or fall back to entering its address."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=TITLE, data={CONF_ADDRESS: address})

        current = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, connectable=False):
            address = info.address.upper()
            if info.name == LOCAL_NAME and address not in current:
                self._discovered[address] = f"{info.name} ({address})"
        if not self._discovered:
            return await self.async_step_manual()
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {probatio.Required(CONF_ADDRESS): probatio.In(self._discovered)}
            ),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter the address of a probe that is not advertising right now."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()
            if not MAC_PATTERN.fullmatch(address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=TITLE, data={CONF_ADDRESS: address}
                )
        return self.async_show_form(
            step_id="manual",
            data_schema=probatio.Schema({probatio.Required(CONF_ADDRESS): str}),
            errors=errors,
        )
