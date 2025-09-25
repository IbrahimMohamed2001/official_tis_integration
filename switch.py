"""Switch platform for TIS Control."""

from __future__ import annotations

from typing import Any

from TISApi.api import TISApi
from TISApi.components.switch.base_switch import BaseTISSwitch
from TISApi.utils import async_get_switches

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TISConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: TISConfigEntry, async_add_devices: AddEntitiesCallback
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
    async_add_devices(tis_switches, update_before_add=True)


class TISSwitch(SwitchEntity, BaseTISSwitch):
    """Represents a TIS switch entity in Home Assistant.

    Inherits from BaseTISSwitch (for API communication) and SwitchEntity (for HA integration).
    """

    def __init__(self, tis_api: TISApi, **kwargs: Any) -> None:
        """Initialize the switch entity."""
        # Pass the core device identifiers to the parent API class.
        super().__init__(
            tis_api=tis_api,
            channel_number=kwargs.get("channel_number", 0),
            device_id=kwargs.get("device_id", []),
            gateway=kwargs.get("gateway", ""),
            is_protected=kwargs.get("is_protected", False),
        )
        # Set the friendly name for the Home Assistant UI.
        self._name = kwargs.get("switch_name", "")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # Attempt to turn the switch on and wait for the result.
        result = await self.turn_switch_on(**kwargs)
        if result:
            # Optimistic update: assume the command succeeded if we got an ack.
            self._state = STATE_ON
        else:
            # If no ack was received, the device is likely offline.
            self._state = STATE_UNKNOWN
            # Fire an event to notify other entities that this device is offline.
            event_data = {
                "device_id": self.device_id,
                "feedback_type": "offline_device",
            }
            self.hass.bus.async_fire(str(self.device_id), event_data)

        # Schedule a state update in Home Assistant's UI.
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # Send the 'off' packet and wait for an acknowledgement.
        result = await self.turn_switch_off(**kwargs)

        # Optimistically update the state based on whether the command was acknowledged.
        self._state = STATE_OFF if result else STATE_UNKNOWN
        self.schedule_update_ha_state()

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
        """Return the current state of the switch (True if on, False if off)."""
        return self._state == STATE_ON
