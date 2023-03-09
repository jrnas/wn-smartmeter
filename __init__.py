"""WienerNetze Sensor custom integration"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import WienerNetzeUpdateCoordinator

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    coordinator: WienerNetzeUpdateCoordinator = WienerNetzeUpdateCoordinator(
        hass, config_entry
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = coordinator

    hass.config_entries.async_setup_platforms(config_entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(
        config_entry, ["sensor"]
    ):
        del hass.data[DOMAIN]

    return unloaded
