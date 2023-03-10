"""Adds config flow for WienerNetze."""
from __future__ import annotations

from typing import Any
import voluptuous as vol
import logging
from .api import WienerNetzeAPI

from homeassistant.core import callback
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
)
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_ZAEHLERPUNKT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class WienerNetzeFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for WienerNetze."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Step user")
        errors = {}

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

            errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default="",
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default="",
                    ): str,
                    vol.Required(
                        CONF_ZAEHLERPUNKT,
                        default="",
                    ): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            ),
            errors=errors,
        )

    async def _test_credentials(self, username, password, zaehlerpunkt):
        """Return true if credentials is valid."""
        _LOGGER.debug("Testing credentials")

        wienernetze_api = WienerNetzeAPI(self.hass, username, password, zaehlerpunkt)
        return await wienernetze_api.login()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        """Options callback for WienerNetze."""
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ZAEHLERPUNKT,
                    default=config_entry.data.get(CONF_ZAEHLERPUNKT, ""),
                ): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        options_flow = {
            "init": SchemaFlowFormStep(options_schema),
        }
        return SchemaOptionsFlowHandler(config_entry, options_flow)
