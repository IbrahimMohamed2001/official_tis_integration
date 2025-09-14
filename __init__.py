"""The TISControl integration."""

from __future__ import annotations

import logging
from attr import dataclass
from TISApi.api import TISApi

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DEVICES_DICT, DOMAIN


@dataclass
class TISData:
    """TISControl data stored in the ConfigEntry."""

    api: TISApi


# Define the Home Assistant platforms that this integration will support.
PLATFORMS: list[Platform] = [Platform.SWITCH]
# Create a type alias for a ConfigEntry specific to this integration.
type TISConfigEntry = ConfigEntry[TISApi]


async def async_setup_entry(hass: HomeAssistant, entry: TISConfigEntry) -> bool:
    """Set up TISControl from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the TIS API with configuration data from the user's entry.
    tis_api = TISApi(
        port=int(entry.data.get("port")),
        hass=hass,
        domain=DOMAIN,
        devices_dict=DEVICES_DICT,
    )
    # Store the API object in the config entry so it can be accessed by platforms.
    entry.runtime_data = TISData(api=tis_api)

    try:
        # Establish a connection to the TIS gateway.
        await tis_api.connect()
    except ConnectionError as e:
        # If connection fails, raise ConfigEntryNotReady to prompt Home Assistant to retry setup later.
        logging.error(f"Failed to connect: {e}")
        raise ConfigEntryNotReady from e
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TISConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload the platforms associated with this entry, which will remove the entities.
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return unload_ok

    return False
