"""Config flow for TISIntegration integration."""

from __future__ import annotations

import logging
from . import DOMAIN
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PORT, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback


_LOGGER = logging.getLogger(__name__)

port_schema = vol.Schema({vol.Required(CONF_PORT): int}, required=True)

auth_schema = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    },
    required=True,
)


class TISConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TISIntegration."""

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is not None:
            logging.info(f"recieved user input {user_input}")
            is_valid = await self.validate_port(user_input[CONF_PORT])
            if not is_valid:
                errors["base"] = "invalid_port"
                logging.error(f"Provided port is invalid: {user_input[CONF_PORT]}")

            if not errors:
                return self.async_create_entry(
                    title="TIS Integration Bridge", data=user_input
                )
            else:
                logging.error(f"Errors occurred: {errors}")
                return self._show_setup_port_form(errors)
        return self._show_setup_auth_form(errors=errors)

    @callback
    def _show_setup_port_form(self, errors=None) -> ConfigFlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=port_schema,
            errors=errors if errors else {},
        )

    @callback
    def _show_setup_auth_form(self, errors=None) -> ConfigFlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=auth_schema,
            errors=errors if errors else {},
        )

    async def validate_port(self, port: int) -> bool:
        """Validate the port."""
        if isinstance(port, int):
            if 1 <= port <= 65535:
                return True
        return False
