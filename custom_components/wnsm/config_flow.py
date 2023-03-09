"""Adds config flow for WienerNetze."""
from __future__ import annotations

from typing import Any
import voluptuous as vol
import logging
from collections import OrderedDict

from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)

from .const import (
    DOMAIN,
    NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_ZAEHLERPUNKT,
    CONF_SCAN_INTERVAL,
)

from .api import WienerNetzeAPI

_LOGGER = logging.getLogger(__name__)


class WienerNetzeFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for WienerNetze."""

    def __init__(self):
        """Initialize the WienerNetze config flow."""
        self._errors = {}

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Step user")

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_ZAEHLERPUNKT],
            )
            _LOGGER.debug("Testing of credentials returned: ")
            _LOGGER.debug(valid)
            if valid:
                return self.async_create_entry(title=NAME, data=user_input)

            self._errors["base"] = "auth"
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit the data."""
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_USERNAME, default="")] = str
        data_schema[
            vol.Required(
                CONF_PASSWORD,
                default="",
            )
        ] = str
        data_schema[vol.Required(CONF_ZAEHLERPUNKT, default="")] = str
        data_schema[vol.Required(CONF_SCAN_INTERVAL, default=60)] = int

        _LOGGER.debug("config form")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password, zaehlerpunkt):
        """Return true if credentials is valid."""
        _LOGGER.debug("Testing credentials")

        wienernetze_api = WienerNetzeAPI(self.hass, username, password, zaehlerpunkt)
        return await wienernetze_api.login()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WienerNetzeOptionsFlowHandler:
        """Get the options flow for this handler."""
        return WienerNetzeOptionsFlowHandler(config_entry)


class WienerNetzeOptionsFlowHandler(OptionsFlow):
    """Handle WienerNetze options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage WienerNetze options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Required(
                CONF_ZAEHLERPUNKT,
                default=self.config_entry.options.get(
                    CONF_ZAEHLERPUNKT, self.config_entry.data[CONF_ZAEHLERPUNKT]
                ),
            ): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, self.config_entry.data[CONF_SCAN_INTERVAL]
                ),
            ): int,
        }

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options), errors=errors
        )
