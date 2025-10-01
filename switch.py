"""Switch platform for TIS Control."""

from __future__ import annotations

from typing import Any

from TISApi.api import TISApi
from TISApi.components.switch.base_switch import BaseTISSwitch
from TISApi.utils import async_get_switches

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TISConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TISConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the TIS switches from a config entry."""

    # Retrieve the API instance that was created in the main __init__.py
    tis_api: TISApi = entry.runtime_data.api

    # Fetch all available switches from the TIS gateway.
    switch_dicts = await async_get_switches(tis_api)
    if not switch_dicts:
        return

    # Create an entity object for each switch found and add them to Home Assistant.
    tis_switches = [TISSwitch(tis_api, **sd) for sd in switch_dicts]
    async_add_entities(tis_switches, update_before_add=True)


class TISSwitch(SwitchEntity, BaseTISSwitch):
    """Represents a TIS switch entity in Home Assistant.

    Inherits from BaseTISSwitch (for API communication) and SwitchEntity (for HA integration).
    """

    def __init__(self, tis_api: TISApi, **kwargs: Any) -> None:
        """Initialize the switch entity."""
        device_id_list = kwargs.get("device_id", [])
        channel = kwargs.get("channel_number", 0)
        gateway = kwargs.get("gateway", "")

        # Pass the core device identifiers to the parent API class.
        super().__init__(
            tis_api=tis_api,
            channel_number=channel,
            device_id=device_id_list,
            gateway=gateway,
            is_protected=kwargs.get("is_protected", False),
        )

        # Set the friendly name for the Home Assistant UI.
        self._attr_name = kwargs.get("switch_name", "")
        self._attr_unique_id = (
            f"tis_{'_'.join(map(str, device_id_list))}_ch{int(channel)}"
        )

        self._attr_available = True
        self._attr_is_on = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # Attempt to turn the switch on and wait for the result.
        result = await self.turn_switch_on(**kwargs)

        if result:
            # Optimistic update: assume the command succeeded if we got an ack.
            self._attr_is_on = True
            self._attr_available = True
        else:
            # If no ack was received, the device is likely offline.
            self._attr_available = False

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # Send the 'off' packet and wait for an acknowledgement.
        result = await self.turn_switch_off(**kwargs)

        # Optimistically update the state based on whether the command was acknowledged.
        if result:
            self._attr_is_on = False
            self._attr_available = True
        else:
            self._attr_available = False

        self.async_write_ha_state()
