"""EmmeTI Febos integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import LOGGER, PLATFORMS
from .coordinator import FebosDataUpdateCoordinator
from .session import FebosSession


def create_session(username: str, password: str) -> FebosSession | None:
    """Create and authenticate a Febos session.

    Args:
        username: The username for Febos login.
        password: The password for Febos login.

    Returns:
        A FebosSession object if successful, None if login fails due to authentication or connection error.
    """
    try:
        session = FebosSession(username=username, password=password)
        session.login()
        return session  # noqa: TRY300
    except Exception as e:  # noqa: BLE001
        LOGGER.error(f"Failed to create session for user '{username}': {e}")
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[FebosDataUpdateCoordinator]
) -> bool:
    """Set up EmmeTI Febos API from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry with username and password credentials.

    Returns:
        True if setup was successful, False otherwise.
    """
    LOGGER.debug("Setup entry started")
    session = await hass.async_add_executor_job(
        create_session, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )
    if session is None:
        LOGGER.debug("Setup entry has failed")
        return False
    entry.runtime_data = FebosDataUpdateCoordinator(hass, entry, session)
    await entry.runtime_data.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    LOGGER.debug("Setup entry terminated successfully")
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry[FebosDataUpdateCoordinator]
) -> bool:
    """Unload a config entry and clean up resources.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry to unload.

    Returns:
        True if unload was successful, False otherwise.
    """
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    LOGGER.debug(
        f"Unload entry {'terminated successfully' if result else 'has failed'}"
    )
    return result
