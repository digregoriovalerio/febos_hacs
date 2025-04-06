"""EmmeTI Febos Binary Sensor definitions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER
from .coordinator import FebosConfigEntry, FebosDataUpdateCoordinator
from .febos import FebosResourceData


class FebosBinarySensorEntity(
    CoordinatorEntity[FebosDataUpdateCoordinator], BinarySensorEntity
):
    """Defines an EmmeTI Febos binary sensor."""

    def __init__(
        self,
        coordinator: FebosDataUpdateCoordinator,
        key: str,
        device_info: DeviceInfo,
        resource: FebosResourceData,
    ) -> None:
        """Initialize EmmeTI Febos sensor."""
        super().__init__(coordinator)
        self._attr_should_poll = False
        self.entity_description = BinarySensorEntityDescription(
            key=key, name=resource.name, device_class=resource.sensor_class
        )
        self._attr_unique_id = key
        self._attr_device_info = device_info
        self._attr_name = resource.name
        self.resource = resource

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.resource.get_value()

    @staticmethod
    def create(
        key: str, resource: FebosResourceData, coordinator: FebosDataUpdateCoordinator
    ):
        """Create an EmmeTI Febos sensor entity."""
        entity = FebosBinarySensorEntity(
            coordinator=coordinator,
            key=key,
            device_info=coordinator.client.services["_".join(key.split("_")[:-1])],
            resource=resource,
        )
        resource.listener = entity.schedule_update_ha_state
        return entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FebosConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a config entry."""
    sensors = [
        FebosBinarySensorEntity.create(k, r, entry.runtime_data)
        for k, r in entry.runtime_data.client.resources.items()
        if r.type == Platform.BINARY_SENSOR and r.value is not None
    ]
    LOGGER.debug(f"Loading {len(sensors)} binary sensors.")
    async_add_entities(sensors)
