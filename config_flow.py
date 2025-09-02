"""Config flow for TISIntegration integration."""

from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PORT, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TISApi
from . import DOMAIN

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

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> ConfigFlowResult:
        """
        Handle a flow initiated by the user.

        Sequence:
            1) show auth form (email/password)
            2) on successful auth -> show port form
            3) on port submit -> create entry with email/password/port
        """
        errors: Dict[str, str] = {}
        description_placeholders: Dict[str, str] = {}

        # First time: show auth form
        if user_input is None:
            return self._show_setup_auth_form()

        # If user_input contains email -> user submitted the auth form
        if CONF_EMAIL in user_input:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            _LOGGER.debug("Received auth input for email=%s", email)

            payload = {"email": email, "password": password}
            endpoint = f"{TISApi}/verify-credentials"
            session = async_get_clientsession(self.hass)

            async with session.post(endpoint, json=payload) as resp:
                status = resp.status
                try:
                    body = await resp.json()
                except Exception:
                    body = {"message": await resp.text()}

                if status == 200:
                    token = body.get("token")
                    if not token:
                        errors["base"] = "unknown"
                    else:
                        # Save the authenticated credentials temporarily and show port form
                        self._auth_data = {CONF_EMAIL: email, CONF_PASSWORD: password}
                        self._token = token
                        return self._show_setup_port_form()

                elif status == 400:
                    # validation error from Laravel. We show a generic field error.
                    # if you want to show the server message in the form, use description_placeholders
                    errors["base"] = "invalid_input"
                    description_placeholders["error"] = body.get(
                        "message", "Invalid input"
                    )
                elif status == 401:
                    errors["base"] = "invalid_auth"
                elif status == 429:
                    errors["base"] = "too_many_requests"
                    description_placeholders["error"] = body.get(
                        "message", "Too many attempts"
                    )
                else:
                    errors["base"] = "unknown"
                    description_placeholders["error"] = body.get(
                        "message", f"HTTP {status}"
                    )

                _LOGGER.warning("Authentication failed for %s", email)
                return self._show_setup_auth_form(
                    errors=errors, description_placeholders=description_placeholders
                )

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
            if not self.validate_port(port):
                errors["base"] = "invalid_port"
                _LOGGER.error("Provided port is invalid: %s", port)
                return self._show_setup_port_form(errors=errors)

            # Merge auth data + port and create config entry
            entry_data = {
                **self._auth_data,
                "token": self._token,
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
    def _show_setup_auth_form(
        self, errors=None, description_placeholders=None
    ) -> ConfigFlowResult:
        """Show the auth (email/password) form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=auth_schema,
            errors=errors if errors else {},
            description_placeholders=(
                description_placeholders if description_placeholders else {}
            ),
        )

    def validate_port(self, port: int) -> bool:
        """Validate the port number range."""
        if isinstance(port, int) and 1 <= port <= 65535:
            return True
        return False
