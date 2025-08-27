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

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow and temporary storage for auth data."""
        self._auth_data: dict | None = None

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """
        Handle a flow initiated by the user.

        Sequence:
            1) show auth form (email/password)
            2) on successful auth -> show port form
            3) on port submit -> create entry with email/password/port
        """
        errors: dict = {}

        # First time: show auth form
        if user_input is None:
            return self._show_setup_auth_form()

        # If user_input contains email -> user submitted the auth form
        if CONF_EMAIL in user_input:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Do NOT log passwords in real code
            _LOGGER.debug("Received auth input for email=%s", email)

            auth_ok = await self.async_validate_credentials(email, password)
            if not auth_ok:
                errors["base"] = "auth_failed"
                _LOGGER.warning("Authentication failed for %s", email)
                return self._show_setup_auth_form(errors=errors)

            # Save the authenticated credentials temporarily and show port form
            self._auth_data = {CONF_EMAIL: email, CONF_PASSWORD: password}
            return self._show_setup_port_form()

        # If user_input contains port -> user submitted the port form
        if CONF_PORT in user_input:
            # Ensure we have auth data from previous step
            if not self._auth_data:
                # This should not normally happen if UI flow is used correctly,
                # but handle it defensively by asking for auth again.
                errors["base"] = "auth_required"
                _LOGGER.error(
                    "Port submitted before authentication; sending user back to auth form"
                )
                return self._show_setup_auth_form(errors=errors)

            port = user_input[CONF_PORT]
            if not await self.validate_port(port):
                errors["base"] = "invalid_port"
                _LOGGER.error("Provided port is invalid: %s", port)
                return self._show_setup_port_form(errors=errors)

            # Merge auth data + port and create config entry
            entry_data = {
                **self._auth_data,
                CONF_PORT: port,
            }

            # Make a meaningful title; you can change as needed
            title = f"TIS Integration ({self._auth_data[CONF_EMAIL]})"

            return self.async_create_entry(title=title, data=entry_data)

        # Fallback - show auth form
        return self._show_setup_auth_form()

    @callback
    def _show_setup_port_form(self, errors=None) -> ConfigFlowResult:
        """Show the port form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=port_schema,
            errors=errors if errors else {},
        )

    @callback
    def _show_setup_auth_form(self, errors=None) -> ConfigFlowResult:
        """Show the auth (email/password) form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=auth_schema,
            errors=errors if errors else {},
        )

    async def validate_port(self, port: int) -> bool:
        """Validate the port number range."""
        if isinstance(port, int) and 1 <= port <= 65535:
            return True
        return False

    async def async_validate_credentials(self, email: str, password: str) -> bool:
        """
        Validate email/password with your bridge/service.

        Replace this placeholder with a real call to the device/cloud.
        Return True on success, False on failure.
        """
        # Example placeholder logic (always fail if empty):
        if not email or not password:
            return False

        # TODO: replace with real async authentication:
        # e.g. await self.hass.async_add_executor_job(sync_client.login, email, password)
        # or call an async HTTP client here.
        # For now return True to continue the flow during testing:
        return True
