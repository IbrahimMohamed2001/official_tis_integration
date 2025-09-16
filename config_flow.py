"""Config flow for TISControl integration."""

from __future__ import annotations
import logging
import voluptuous as vol
from .const import DOMAIN
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PORT
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)


class TISConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TISControl."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            logging.info(f"recieved user input {user_input}")
            # Assuming a function `validate_port` that returns True if the port is valid
            is_valid = await self.validate_port(user_input[CONF_PORT])
            if not is_valid:
                errors["base"] = "invalid_port"  # Custom error key
                logging.error(f"Provided port is invalid: {user_input[CONF_PORT]}")

            if not errors:
                return self.async_create_entry(
                    title="TIS Control Bridge", data=user_input
                )
            else:
                # If there are errors, show the form again with the error message
                logging.error(f"Errors occurred: {errors}")
                return self._show_setup_form(errors)

        # If user_input is None (initial step), show the setup form
        return self._show_setup_form(errors=errors)

    @callback
    def _show_setup_form(self, errors=None) -> ConfigFlowResult:
        """Show the setup form to the user."""

        schema = vol.Schema(
            {vol.Required(CONF_PORT, default=6000): int},
            required=True,
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors if errors else {},
        )

    async def validate_port(self, port: int) -> bool:
        """Validate the port."""
        if isinstance(port, int):
            if 1 <= port <= 65535:
                return True
        return False
