"""Entity for WienerNetze."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import WienerNetzeUpdateCoordinator


class WienerNetzeEntity(CoordinatorEntity[WienerNetzeUpdateCoordinator]):
    """WienerNetze base entity definition."""

    def __init__(
        self,
        coordinator: WienerNetzeUpdateCoordinator,
        description: EntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_name = description.name
        self._attr_unique_id = f"{config_entry.entry_id}{description.key.lower()}"
        self.entity_description = description
