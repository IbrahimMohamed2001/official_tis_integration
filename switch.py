"""Switch platform for TIS Control."""

from __future__ import annotations

from collections.abc import Callable
from math import ceil
from typing import Any, Optional

from TISApi.BytesHelper import int_to_8_bit_binary
from TISApi.api import TISApi
from TISApi.Protocols.udp.ProtocolHandler import (
    TISPacket,
    TISProtocolHandler,
)

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import MATCH_ALL, STATE_OFF, STATE_ON, STATE_UNKNOWN, Platform
from homeassistant.core import Event, HomeAssistant, callback
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


async def async_get_switches(tis_api: TISApi) -> list[dict]:
    """Fetch switches from TIS API and normalize to a list of dictionaries.

    Returns a list with items like:
    {
        "switch_name": str,
        "channel_number": int,
        "device_id": list[int],
        "is_protected": bool,
        "gateway": str,
    }

    Having this helper makes the setup code easier to test and keeps the
    API parsing logic in one place.
    """
    raw = await tis_api.get_entities(platform=Platform.SWITCH)
    if not raw:
        return []

    result: list[dict] = []
    for appliance in raw:
        channel_number = int(list(appliance["channels"][0].values())[0])
        result.append(
            {
                "switch_name": appliance.get("name"),
                "channel_number": channel_number,
                "device_id": appliance.get("device_id"),
                "is_protected": appliance.get("is_protected", False),
                "gateway": appliance.get("gateway"),
            }
        )

    return result


class BaseTISSwitch:
    """Base class for TIS switches."""

    def __init__(
        self,
        tis_api: TISApi,
        *,
        channel_number: int,
        device_id: list[int],
        gateway: str,
        is_protected: bool = False,
        **kwargs: Any,
    ) -> None:
        # Call next class in MRO (important for multiple inheritance)
        super().__init__(**kwargs)

        self.api = tis_api

        # Internal state representation
        self._state = STATE_UNKNOWN
        self._attr_is_on: Optional[bool] = None

        self._attr_unique_id = (
            f"tis_{'_'.join(map(str, device_id))}_ch{int(channel_number)}"
        )

        self.device_id = device_id
        self.gateway = gateway
        self.channel_number = int(channel_number)
        self.is_protected = is_protected

        self._listener: Optional[Callable] = None

        # Pre-generate packets
        self.on_packet = TISProtocolHandler.generate_control_on_packet(self)
        self.off_packet = TISProtocolHandler.generate_control_off_packet(self)
        self.update_packet = TISProtocolHandler.generate_control_update_packet(self)

    # --- Lifecycle hooks ---
    async def async_added_to_hass(self) -> None:
        """Subscribe to events when the entity is added to hass."""

        @callback
        def _handle_event(event: Event) -> None:
            """Handle incoming TIS events and update internal state accordingly."""

            # check if event is for this switch
            if event.event_type == str(self.device_id):
                feedback_type = event.data.get("feedback_type")
                if feedback_type == "control_response":
                    channel_value = event.data["additional_bytes"][2]
                    channel_number = event.data["channel_number"]
                    if int(channel_number) == self.channel_number:
                        self._state = (
                            STATE_ON if int(channel_value) == 100 else STATE_OFF
                        )

                elif feedback_type == "binary_feedback":
                    n_bytes = ceil(event.data["additional_bytes"][0] / 8)
                    channels_status = "".join(
                        int_to_8_bit_binary(event.data["additional_bytes"][i])
                        for i in range(1, n_bytes + 1)
                    )
                    self._state = (
                        STATE_ON
                        if channels_status[self.channel_number - 1] == "1"
                        else STATE_OFF
                    )

                elif feedback_type == "update_response":
                    additional_bytes = event.data["additional_bytes"]
                    channel_status = int(additional_bytes[self.channel_number])
                    self._state = STATE_ON if channel_status > 0 else STATE_OFF

                elif feedback_type == "offline_device":
                    self._state = STATE_UNKNOWN

            self.schedule_update_ha_state()

        self._listener = self.hass.bus.async_listen(MATCH_ALL, _handle_event)
        _ = await self.api.protocol.sender.send_packet(self.update_packet)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from events when entity is removed from hass."""
        if callable(self._listener):
            try:
                self._listener()
            finally:
                self._listener = None

    # --- Control methods ---
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (uses API send with ack)."""
        ack_status = await self.api.protocol.sender.send_packet_with_ack(self.on_packet)
        if ack_status:
            self._state = STATE_ON
        else:
            self._state = STATE_UNKNOWN
            event_data = {
                "device_id": self.device_id,
                "feedback_type": "offline_device",
            }
            self.hass.bus.async_fire(str(self.device_id), event_data)
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (uses API send with ack)."""
        ack_status = await self.api.protocol.sender.send_packet_with_ack(
            self.off_packet
        )
        if ack_status:
            self._state = STATE_OFF
        else:
            self._state = STATE_UNKNOWN
        self.schedule_update_ha_state()


class TISSwitch(SwitchEntity, BaseTISSwitch):
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

    # --- Properties ---
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
