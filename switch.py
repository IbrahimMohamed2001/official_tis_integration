"""Switch platform for TIS Control."""

from __future__ import annotations

from typing import Any

from TISApi.api import TISApi
from TISApi.utils import async_get_switches
from TISApi.components.switch.base_switch import BaseTISSwitch

from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TISConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: TISConfigEntry, async_add_devices: AddEntitiesCallback
) -> None:
    """Set up the TIS switches."""

    # getting the tis_api object from the config entry
    tis_api: TISApi = entry.runtime_data.api

    # Fetch and normalize switches into simple dictionaries
    switch_dicts = await async_get_switches(tis_api)
    if not switch_dicts:
        return

    # Create TISSwitch objects using **kwargs for readability
    tis_switches = [TISSwitch(tis_api, **sd) for sd in switch_dicts]
    async_add_devices(tis_switches, update_before_add=True)


class TISSwitch(BaseTISSwitch, SwitchEntity):
    """Concrete TIS switch entity."""

    def __init__(self, tis_api: TISApi, **kwargs: Any) -> None:
        super().__init__(
            tis_api=tis_api,
            channel_number=kwargs.get("channel_number"),
            device_id=kwargs.get("device_id"),
            gateway=kwargs.get("gateway"),
            is_protected=kwargs.get("is_protected", False),
        )
        self._name = kwargs.get("switch_name")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the switch."""
        self._name = value

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return self._state == STATE_ON
