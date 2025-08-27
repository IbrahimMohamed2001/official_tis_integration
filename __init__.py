"""The TISControl integration."""

from __future__ import annotations

# import logging
# import os
# import aiofiles, json
# import io
# from attr import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

DOMAIN = "tis_integration"


# @dataclass
# class TISData:
#     """TISControl data stored in the ConfigEntry."""
#     api: TISApi


PLATFORMS: list[Platform] = [
    Platform.SWITCH,
]


async def async_setup_entry(hass, entry):
    """Set up TISControl from a config entry."""
    pass


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    pass
