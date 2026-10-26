"""The RC-C Solar (rc-ess) integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RcEssApiError, RcEssAuthError, RcEssClient
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RC-C Solar from a config entry."""
    session = async_get_clientsession(hass)
    client = RcEssClient(session, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])

    interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    async def _async_update_data() -> dict[str, dict]:
        try:
            result: dict[str, dict] = {}
            for device in await client.async_discover():
                data = await client.async_get_device_data(device["id"])
                data["_station_name"] = device.get("_station_name")
                data["sn"] = device.get("sn")
                result[device["id"]] = data
            return result
        except RcEssAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication error: {err}") from err
        except RcEssApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

    coordinator: DataUpdateCoordinator[dict[str, dict]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_data,
        update_interval=timedelta(seconds=interval),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
