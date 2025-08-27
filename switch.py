"""Switch platform for integration_blueprint."""

from __future__ import annotations

from collections.abc import Callable
from math import ceil
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import MATCH_ALL, STATE_OFF, STATE_ON, STATE_UNKNOWN, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging


async def async_setup_entry(hass, entry, async_add_devices) -> None:
    """Set up the TIS switches."""
    pass


class TISSwitch(SwitchEntity):
    """Representation of a TIS switch."""

    def __init__(
        self,
    ) -> None:
        """Initialize the switch."""
        pass

    async def async_added_to_hass(self) -> None:
        """Subscribe to events."""
        pass

    async def async_will_remove_from_hass(self) -> None:
        """Remove the listener when the entity is removed."""
        pass
        self.listener = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        pass

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        pass

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the switch."""
        self._name = value

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._attr_unique_id

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        if self._state == STATE_ON:
            return True

        elif self._state == STATE_OFF:
            return False

        else:
            return None
