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
        _LOGGER.debug("scan_interval: %s", self.config_entry.data[CONF_SCAN_INTERVAL])
        self.wienernetze_api = WienerNetzeAPI(
            hass,
            self.config_entry.data[CONF_USERNAME],
            self.config_entry.data[CONF_PASSWORD],
            self.config_entry.data[CONF_METER_READER],
        )

        self.entities: list[Entity] = []

    async def _update_meterreader(self, data):
        _LOGGER.debug("_update_meterreader()")
        response = await self.wienernetze_api.get_meter_reader()
        _LOGGER.debug(response)
        data[ATTR_METER_READER] = response["meterReadings"][0]["value"] / 1000

    async def _update_consumption(self, data):
        _LOGGER.debug("_update_consumption()")
        response = await self.wienernetze_api.get_consumption(
            self.config_entry.data[CONF_METER_READER]
        )
        _LOGGER.debug(response)
        if response is not None and hasattr(response, "get"):
            values = response.get("values")
            if values:
                for value in values:
                    if value is not None:
                        val = value.get("value") / 1000
                        timestamp = value.get("timestamp")

                        if val and timestamp:
                            t_z = pytz.timezone(TIMEZONE)
                            now = datetime.now(tz=t_z)
                            yesterday = now - timedelta(days=1)
                            day_before_yesterday = now - timedelta(days=2)

                            timestamp = parse(timestamp) + timedelta(days=1)
                            if timestamp.date() == yesterday.date():
                                data[ATTR_CONSUMPTION_YESTERDAY] = val
                            if timestamp.date() == day_before_yesterday.date():
                                data[ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY] = val

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data."""
        data: dict[str, Any] = {}

        await self._update_meterreader(data)
        await self._update_consumption(data)

        _LOGGER.debug(data)
        return data
