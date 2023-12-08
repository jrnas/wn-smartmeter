"""Adds config flow for WienerNetze."""
from __future__ import annotations

from typing import Any
import logging
import voluptuous as vol

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

from .api import WienerNetzeAPI

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_METER_READER,
    CONF_CUSTOMER_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class WienerNetzeFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for WienerNetze."""

    VERSION = 1
    _previous_input: dict[str, Any]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Step user")
        errors = {}

        if user_input is not None:
            api = WienerNetzeAPI(
                self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            valid = await self._test_credentials(api)
            _LOGGER.debug("Testing of credentials returned: ")
            _LOGGER.debug("logged in: %s", valid)
            if valid:
                self._previous_input = user_input
                return await self.async_step_select_meter_reader(user_input=user_input)

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
                }
            ),
            errors=errors,
        )

    async def async_step_select_meter_reader(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Step select meter reader")
        errors = {}

        if CONF_METER_READER in user_input:
            user_input.update(self._previous_input)
            return self.async_create_entry(
                title=user_input[CONF_METER_READER], data=user_input
            )
        else:
            api = WienerNetzeAPI(
                self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            response = await self._get_meter_readers(api)
            _LOGGER.debug(response)
            meter_readers = response[0]
            customerId = response[0]["geschaeftspartner"]
            _LOGGER.debug(customerId)
            if "zaehlpunkte" not in meter_readers:
                _LOGGER.error("no meter readers found.")

        return self.async_show_form(
            step_id="select_meter_reader",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_METER_READER,
                        default="",
                    ): vol.In(
                        {
                            meter_reader["zaehlpunktnummer"]
                            for meter_reader in meter_readers["zaehlpunkte"]
                        }
                    ),
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                    vol.Required(
                        CONF_CUSTOMER_ID, default=customerId
                    ): str,
                }
            ),
            errors=errors,
            last_step=True,
        )

    async def _test_credentials(self, api: WienerNetzeAPI):
        """Return true if credentials is valid."""
        _LOGGER.debug("Testing credentials")

        return await api.login()

    async def _get_meter_readers(self, api: WienerNetzeAPI):
        """Return a list of meter readers."""
        _LOGGER.debug("Get meter readers")
        return await api.get_meter_readers()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        """Options callback for WienerNetze."""
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_METER_READER,
                    default=config_entry.data.get(CONF_METER_READER, ""),
                ): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        options_flow = {
            "init": SchemaFlowFormStep(options_schema),
        }
        return SchemaOptionsFlowHandler(config_entry, options_flow)
