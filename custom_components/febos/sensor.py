"""EmmeTI Febos sensor definitions."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER
from .coordinator import FebosDataUpdateCoordinator
from .entities import FebosSensorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FebosDataUpdateCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Febos sensor entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry with Febos integration data.
        async_add_entities: Callback to add new entities.
    """
    entities = [
        FebosSensorEntity(coordinator=entry.runtime_data, input=i)
        for i in entry.runtime_data.session.sensors
    ]
    LOGGER.info(f"Loading {len(entities)} sensors.")
    async_add_entities(entities)
