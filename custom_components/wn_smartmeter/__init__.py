"""WienerNetze Sensor custom integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import WienerNetzeUpdateCoordinator

from .const import DOMAIN
from .const import CONF_METER_READER, CONF_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    coordinator: WienerNetzeUpdateCoordinator = WienerNetzeUpdateCoordinator(
        hass, config_entry
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(
        config_entry, ["sensor"]
    ):
        del hass.data[DOMAIN]

    return unloaded


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener."""
    _LOGGER.debug("update_listener()")
    if CONF_SCAN_INTERVAL in config_entry.options:
        new = {**config_entry.data}
        new[CONF_SCAN_INTERVAL] = config_entry.options[CONF_SCAN_INTERVAL]
        hass.config_entries.async_update_entry(config_entry, data=new)

    if CONF_METER_READER in config_entry.options:
        new = {**config_entry.data}
        new[CONF_METER_READER] = config_entry.options[CONF_METER_READER]
        hass.config_entries.async_update_entry(config_entry, data=new)

    await hass.config_entries.async_reload(config_entry.entry_id)
