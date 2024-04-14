"""Data update coordinator for WienerNetze."""

import logging
from typing import Any
from datetime import timedelta, datetime
from dateutil.parser import parse
import pytz

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    TIMEZONE,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_METER_READER,
    CONF_CUSTOMER_ID,
    CONF_SCAN_INTERVAL,
    ATTR_METER_READER,
    ATTR_CONSUMPTION_YESTERDAY,
    ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY,
)

from .api import WienerNetzeAPI

_LOGGER = logging.getLogger(__name__)


class WienerNetzeUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """WienerNetze data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize WienerNetze data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=config_entry.data[CONF_SCAN_INTERVAL]),
        )
        _LOGGER.debug("setup")
        _LOGGER.debug("meter_reader: %s", self.config_entry.data[CONF_METER_READER])
        _LOGGER.debug("customer_id: %s", self.config_entry.data[CONF_CUSTOMER_ID])
        _LOGGER.debug("scan_interval: %s", self.config_entry.data[CONF_SCAN_INTERVAL])
        self.wienernetze_api = WienerNetzeAPI(
            hass,
            self.config_entry.data[CONF_USERNAME],
            self.config_entry.data[CONF_PASSWORD],
            self.config_entry.data[CONF_METER_READER],
        )

        self.entities: list[Entity] = []

    async def _set_default_meterreader(self):
        _LOGGER.debug("_set_default_meterreader()")
        await self.wienernetze_api.set_default_meterreader(self.config_entry.data[CONF_METER_READER], self.config_entry.data[CONF_CUSTOMER_ID])

    async def _login(self):
        await self.wienernetze_api.login()

    async def _update_meterreader(self, data):
        _LOGGER.debug("_update_meterreader()")
        await self._set_default_meterreader()
        response = await self.wienernetze_api.get_meter_reader()
        _LOGGER.debug(response)
        data[ATTR_METER_READER] = response["meterReadings"][0]["value"] / 1000

    async def _update_consumptions(self, data):
        _LOGGER.debug("_update_consumptions()")
        await self._set_default_meterreader()
        response = await self.wienernetze_api.get_consumptions()
        _LOGGER.debug(response)
        if response is not None and hasattr(response, "get"):
            if response.get("consumptionYesterday") is not None:
                consumptionYesterday = response.get("consumptionYesterday")["value"]
                if consumptionYesterday is not None:
                    data[ATTR_CONSUMPTION_YESTERDAY] = consumptionYesterday / 1000
            if response.get("consumptionDayBeforeYesterday") is not None:
                consumptionDayBeforeYesterday = response.get("consumptionDayBeforeYesterday")["value"]
                if consumptionDayBeforeYesterday is not None:
                    data[ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY] = consumptionDayBeforeYesterday / 1000

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data."""
        data: dict[str, Any] = {}
        await self._login()
        await self._update_meterreader(data)
        await self._update_consumptions(data)

        _LOGGER.debug(data)
        return data
