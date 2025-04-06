"""EmmeTI Febos integration for Home Assistant."""

from febos.api import FebosApi
from febos.errors import FebosError
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import LOGGER, PLATFORMS
from .coordinator import FebosConfigEntry, FebosDataUpdateCoordinator
from .febos import FebosClient


def create_api(username: str, password: str) -> FebosApi:
    try:
        api = FebosApi(username, password)
        api.login()
    except FebosError as e:
        LOGGER.error(str(e))
    else:
        return api
    return None


async def async_setup_entry(hass: HomeAssistant, entry: FebosConfigEntry) -> bool:
    """Set up EmmeTI Febos API from a config entry."""
    api = await hass.async_add_executor_job(
        create_api, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )
    if api is None:
        return False
    client = FebosClient(api=api)
    entry.runtime_data = FebosDataUpdateCoordinator(hass, entry, client)
    await entry.runtime_data.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FebosConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
