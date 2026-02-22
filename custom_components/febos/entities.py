"""EmmeTI Febos entity definitions for sensors and binary sensors."""

from typing import cast

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FebosDataUpdateCoordinator
from .normalization import NormalizedInput


class FebosBinarySensorEntity(  # type: ignore
    CoordinatorEntity[FebosDataUpdateCoordinator], BinarySensorEntity
):
    """Home Assistant binary sensor entity for Febos inputs.

    Wraps a NormalizedInput and exposes its state and device info to Home Assistant.
    Availability is based on both the coordinator's last update and the input value.
    """

    def __init__(
        self,
        coordinator: FebosDataUpdateCoordinator,
        input: NormalizedInput,
    ) -> None:
        """Initialize a Febos binary sensor entity.

        Args:
            coordinator: The data update coordinator.
            input: The NormalizedInput representing this binary sensor.
        """
        super().__init__(coordinator)
        self.entity_description = BinarySensorEntityDescription(
            key=input.key,
            name=input.label,
            device_class=input.binary_sensor_device_class,
        )
        self._attr_should_poll = False
        self._attr_unique_id = input.key
        self._attr_device_info = input.device_info
        self._attr_name = input.label

    @property
    def is_on(self):
        return self.coordinator.data[self.entity_description.key]

    @property
    def available(self):
        return (
            self.coordinator.last_update_success
            and self.coordinator.data[self.entity_description.key] is not None
        )


class FebosSensorEntity(CoordinatorEntity[FebosDataUpdateCoordinator], SensorEntity):  # type: ignore
    """Home Assistant sensor entity for Febos inputs.

    Wraps a NormalizedInput and exposes its state and device info to Home Assistant.
    Availability is based on both the coordinator's last update and the input value.
    """

    def __init__(
        self,
        coordinator: FebosDataUpdateCoordinator,
        input: NormalizedInput,
    ) -> None:
        """Initialize a Febos sensor entity.

        Args:
            coordinator: The data update coordinator.
            input: The NormalizedInput representing this sensor.
        """
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key=input.key,
            device_class=input.sensor_device_class,
            state_class=input.sensor_state_class,
            native_unit_of_measurement=input.measurement_unit,
        )
        self._attr_should_poll = False
        self._attr_unique_id = input.key
        self._attr_device_info = input.device_info
        self._attr_name = input.label

    @property
    def native_value(self):
        return self.coordinator.data[self.entity_description.key]

    @property
    def available(self):
        return (
            self.coordinator.last_update_success
            and self.coordinator.data[self.entity_description.key] is not None
        )


class FebosSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Home Assistant switch entity for Febos inputs.

    Wraps a NormalizedInput and exposes its state and device info to Home Assistant.
    Availability is based on both the coordinator's last update and the input value.
    It also updates values on change by contacting the the Febos backend.
    """

    def __init__(
        self,
        coordinator: FebosDataUpdateCoordinator,
        input: NormalizedInput,
    ) -> None:
        """Initialize a Febos switch entity.

        Args:
            coordinator: The data update coordinator.
            input: The NormalizedInput representing this switch.
        """
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key=input.key,
            name=input.label,
            device_class=input.switch_device_class,
        )
        self._attr_should_poll = False
        self._attr_unique_id = input.key
        self._attr_device_info = input.device_info
        self._attr_name = input.label

    @property
    def is_on(self):
        return self.coordinator.data[self.entity_description.key]

    @property
    def available(self):
        return (
            self.coordinator.last_update_success
            and self.coordinator.data[self.entity_description.key] is not None
        )

    async def async_turn_on(self, **kwargs):
        coordinator = cast(FebosDataUpdateCoordinator, self.coordinator)
        await coordinator.async_set_value(self.entity_description.key, True)

    async def async_turn_off(self, **kwargs):
        coordinator = cast(FebosDataUpdateCoordinator, self.coordinator)
        await coordinator.async_set_value(self.entity_description.key, False)


class FebosNumberEntity(CoordinatorEntity, NumberEntity):
    """Home Assistant number entity for Febos inputs.

    Wraps a NormalizedInput and exposes its state and device info to Home Assistant.
    Availability is based on both the coordinator's last update and the input value.
    It also updates values on change by contacting the the Febos backend.
    """

    def __init__(
        self,
        coordinator: FebosDataUpdateCoordinator,
        input: NormalizedInput,
    ) -> None:
        """Initialize a Febos number entity.

        Args:
            coordinator: The data update coordinator.
            input: The NormalizedInput representing this number.
        """
        super().__init__(coordinator)
        self.entity_description = NumberEntityDescription(
            key=input.key,
            name=input.label,
            device_class=input.number_device_class,
            native_unit_of_measurement=input.measurement_unit,
        )
        self._attr_should_poll = False
        self._attr_unique_id = input.key
        self._attr_device_info = input.device_info
        self._attr_name = input.label
        if input.min is not None:
            self._attr_native_min_value = float(input.min)
        if input.max is not None:
            self._attr_native_max_value = float(input.max)

    @property
    def native_value(self) -> int:
        return self.coordinator.data[self.entity_description.key]

    @property
    def available(self):
        return (
            self.coordinator.last_update_success
            and self.coordinator.data[self.entity_description.key] is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        coordinator = cast(FebosDataUpdateCoordinator, self.coordinator)
        await coordinator.async_set_value(self.entity_description.key, value)
