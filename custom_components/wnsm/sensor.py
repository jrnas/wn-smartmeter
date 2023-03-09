"""Platform for sensor integration."""
from __future__ import annotations
import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import StateType

from .coordinator import WienerNetzeUpdateCoordinator
from .entity import WienerNetzeEntity
from .custom_components.wnsm.const import (
    DOMAIN,
    ATTR_ZAEHLERPUNKT,
    ATTR_CONSUMPTION_YESTERDAY,
    ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensor platform."""
    coordinator: WienerNetzeUpdateCoordinator = hass.data[DOMAIN]
    _LOGGER.debug("setup")
    entities = []
    for description in SENSORS:
        entity = WienerNetzeSensorEntity(coordinator, description, config)
        coordinator.entities.append(entity)
        entities.append(entity)

    async_add_entities(entities, True)


@dataclass
class WienerNetzeSensorEntityDescription(SensorEntityDescription):
    """WienerNetze sensor entity description."""

    exists_fn: Callable[[list[str]], bool] = lambda _: True
    entity_registry_enabled_default: bool = True


SENSORS: tuple[WienerNetzeSensorEntityDescription, ...] = (
    WienerNetzeSensorEntityDescription(
        key=ATTR_ZAEHLERPUNKT,
        name="WienerNetze Zaehlerstand",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
        exists_fn=lambda entities: ATTR_ZAEHLERPUNKT in entities,
    ),
    WienerNetzeSensorEntityDescription(
        key=ATTR_CONSUMPTION_YESTERDAY,
        name="WienerNetze Consumption yesterday",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
        exists_fn=lambda entities: ATTR_CONSUMPTION_YESTERDAY in entities,
    ),
    WienerNetzeSensorEntityDescription(
        key=ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY,
        name="WienerNetze Consumption day before yesterday",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        exists_fn=lambda entities: ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY in entities,
        icon="mdi:flash",
    ),
)


class WienerNetzeSensorEntity(WienerNetzeEntity, SensorEntity):
    """WienerNetze sensor entity definition."""

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.get(self.entity_description.key, None)
