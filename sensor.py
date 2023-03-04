"""Platform for sensor integration."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.const import UnitOfEnergy

from datetime import timedelta, datetime
import pytz

from .api import WienerNetzeAPI
from dateutil.parser import parse

SCAN_INTERVAL = timedelta(minutes=60)
_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("setup")
    wienernetze = WienerNetze(
        config["username"], config["password"], config["zaehlerpunkt"]
    )
    wienernetze.update()

    add_entities(
        [WienerNetzeZaehlerstand(wienernetze)],
        update_before_add=True,
    )

    add_entities(
        [WienerNetzeYesterday(wienernetze)],
        update_before_add=True,
    )

    add_entities(
        [WienerNetzeDayBeforeYesterday(wienernetze)],
        update_before_add=True,
    )


class WienerNetze(SensorEntity):
    """Representation of WIenerNetze"""

    def __init__(self, username: str, password: str, zaehlerpunkt: str) -> None:
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlerpunkt
        self.zaehlerstand = None
        self.yesterday = None
        self.day_before_yesterday = None

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.zaehlerstand = None
        self.yesterday = None
        self.day_before_yesterday = None
        api = WienerNetzeAPI(self.username, self.password)
        api.login()
        response = api.get_zaehlerstand()
        _LOGGER.debug(response)
        self.zaehlerstand = response["meterReadings"][0]["value"] / 1000

        response = api.get_consumption(self.zaehlpunkt)
        _LOGGER.debug(response)

        if response is not None:
            values = response.get("values")
            if values:
                for value in values:
                    if value is not None:
                        val = value.get("value") / 1000
                        timestamp = value.get("timestamp")

                        if val and timestamp:
                            tZ = pytz.timezone("Europe/Vienna")
                            now = datetime.now(tz=tZ)
                            yesterday = now - timedelta(days=1)
                            day_before_yesterday = now - timedelta(days=2)

                            timestamp = parse(timestamp) + timedelta(days=1)
                            if timestamp.date() == yesterday.date():
                                self.yesterday = val
                            if timestamp.date() == day_before_yesterday.date():
                                self.day_before_yesterday = val


class WienerNetzeZaehlerstand(SensorEntity):
    """Representation of WienerNetze_Zaehlerstand Sensors."""

    def __init__(self, wienernetze: WienerNetze) -> None:
        super().__init__()
        self.wienernetze = wienernetze
        self._attr_native_value = int
        self._attr_name = "WienerNetze Zaehlerstand"
        self._attr_icon = "mdi:flash"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        self.attrs = {}
        self._name: str = "WienerNetze Zaehlerstand"
        self._attr_unique_id = "wienernetze_zaehlerstand"
        self._state: int = None

        self._available = None
        if wienernetze.zaehlerstand is not None:
            if wienernetze.zaehlerstand > 0:
                self._available = True

        self._updatets: str = None

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.wienernetze.update()
        self._attr_native_value = self.wienernetze.zaehlerstand


class WienerNetzeYesterday(SensorEntity):
    """Representation of WienerNetze_Zaehlerstand Sensors."""

    def __init__(self, wienernetze: WienerNetze) -> None:
        super().__init__()
        self.wienernetze = wienernetze
        self._attr_native_value = int
        self._attr_name = "WienerNetze Yesterday"
        self._attr_icon = "mdi:flash"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        self.attrs = {}
        self._name: str = "WienerNetze Yesterday"
        self._attr_unique_id = "wienernetze_yesterday"
        self._state: int = None
        self._available = None
        if wienernetze.yesterday is not None:
            if wienernetze.yesterday > 0:
                self._available = True

        self._updatets: str = None

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = self.wienernetze.yesterday


class WienerNetzeDayBeforeYesterday(SensorEntity):
    """Representation of WienerNetze_Zaehlerstand Sensors."""

    def __init__(self, wienernetze: WienerNetze) -> None:
        super().__init__()
        self.wienernetze = wienernetze
        self._attr_native_value = int
        self._attr_name = "WienerNetze Day Before Yesterday"
        self._attr_icon = "mdi:flash"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        self.attrs = {}
        self._name: str = "WienerNetze Day Before Yesterday"
        self._attr_unique_id = "wienernetze_day_before_yesterday"
        self._state: int = None
        self._available = None
        if wienernetze.day_before_yesterday is not None:
            if wienernetze.day_before_yesterday > 0:
                self._available = True

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = self.wienernetze.day_before_yesterday
