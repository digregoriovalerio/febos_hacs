"""EmmeTI Febos sensor definitions."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER
from .coordinator import FebosConfigEntry, FebosDataUpdateCoordinator
from .febos import FebosResourceData


class FebosSensorEntity(CoordinatorEntity[FebosDataUpdateCoordinator], SensorEntity):
    """Defines an EmmeTI Febos sensor."""

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
        self.entity_description = SensorEntityDescription(
            key=key,
            device_class=resource.sensor_class,
            state_class=resource.state_class,
            native_unit_of_measurement=resource.meas_unit,
        )
        self._attr_unique_id = key
        self._attr_device_info = device_info
        self._attr_name = resource.name
        self.resource = resource

    @property
    def native_value(self) -> Any:
        """Return the value of the sensor."""
        return self.resource.get_value()

    @staticmethod
    def create(
        key: str, resource: FebosResourceData, coordinator: FebosDataUpdateCoordinator
    ):
        """Create an EmmeTI Febos sensor entity."""
        entity = FebosSensorEntity(
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

    def make_sensor(self):
        """Create entities from resources."""

    sensors = [
        FebosSensorEntity.create(k, r, entry.runtime_data)
        for k, r in entry.runtime_data.client.resources.items()
        if r.type == Platform.SENSOR and r.value is not None
    ]
    LOGGER.debug(f"Loading {len(sensors)} sensors.")
    async_add_entities(sensors)
