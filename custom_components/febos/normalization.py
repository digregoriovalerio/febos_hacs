"""EmmeTI Febos data normalization."""

from collections.abc import Callable
from typing import Any

from propcache.api import cached_property

from febos import Input
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.number import NumberDeviceClass

from homeassistant.const import (
    CURRENCY_EURO,
    PERCENTAGE,
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import LOGGER


def int16(v: int):
    """Convert a two's complement 16-bits integer into an int."""
    v = int(v)
    return v if v < 32768 else v - 65536


def tenth(v: int | float) -> float:
    return float(v) / 10.0


def hundred(v: int | float) -> float:
    return float(v) / 100.0


def thousand(v: int | float) -> float:
    return float(v) / 1000.0


def ctwo(v: int) -> float:
    return float(int16(v))


def ctwo_thousand(v: int) -> float:
    return float(int16(v)) / 1000.0


def by_ten(v: int | float) -> float:
    return float(v) * 10.0


def by_sixty(v: int | float) -> float:
    return float(v) * 60.0


class NormalizedInput:
    """Represents a normalized Febos input (sensor or binary sensor).

    Handles value normalization, unit conversion, device classification,
    and entity state mapping for Febos devices. Used as the data model for both
    sensor and binary sensor entities in the Febos integration.
    """

    def __init__(self, key: str, installation_id: int, thing_model_id: int, device_info: DeviceInfo, input_entry: Input) -> None:
        """Initialize a NormalizedInput.

        Args:
            key: Unique identifier for this input.
            installation_id: Identifier of the installation.
            thing_model_id: Model ID of the thing this input belongs.
            device_info: Device information for Home Assistant registry.
            input_entry: The original Febos Input object.
        """
        super().__init__()
        self.key = key
        self.installation_id = installation_id
        self.thing_model_id = thing_model_id
        self.device_info: DeviceInfo = device_info
        self.listener: Callable | None = None
        self._input: Input = input_entry
        self._value: Any = (
            int(self._input.defaultIntValue) if self._input.inputType == "INT" and self._input.defaultIntValue is not None else None
        )

    @property
    def min(self) -> int | None:
        return self._input.min

    @property
    def max(self) -> int | None:
        return self._input.max

    @property
    def code(self) -> str:
        return self._input.code
        
    @property
    def device_id(self) -> int:
        return self._input.deviceId
        
    @property
    def thing_id(self) -> int:
        return self._input.thingId

    @property
    def value(self) -> Any:
        """Get the current value of this input.

        Returns:
            The last value set, after normalization.
        """
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Set the value.

        Args:
            value: The new value to set (will be converted to proper type).
        """
        old_value = self._value
        self._value = self.value_type(value) if value is not None else None
        if old_value != self._value:
            LOGGER.debug(
                f"{self.key}: {old_value} ==> {self._value}"
            )

    @property
    def _scaled_value(self):
        value = self.value
        if value is None:
            return None
        return {
            "R9120": by_sixty,
            "R8208": thousand,
            "R8209": thousand,
            "R8211": thousand,
            "R8212": thousand,
            "R8214": thousand,
            "R8215": thousand,
            "R8217": thousand,
            "R8218": thousand,
            "R8100": tenth,
            "R8665": tenth,
            "R8666": tenth,
            "R8678": tenth,
            "R8680": tenth,
            "R8698": tenth,
            "R8702": tenth,
            "R8703": tenth,
            "R8986": tenth,
            "R8987": tenth,
            "R8988": tenth,
            "R8989": tenth,
            "R9042": tenth,
            "R9051": tenth,
            "R9052": tenth,
            "R16444": tenth,
            "R16446": tenth,
            "R16448": tenth,
            "R16450": tenth,
            "R16451": tenth,
            "R16453": tenth,
            "R16455": tenth,
            "R16457": tenth,
            "R16494": tenth,
            "R16495": tenth,
            "R16496": tenth,
            "R16497": tenth,
            "R16515": tenth,
            "R8684": hundred,
            "R8686": hundred,
            "R8688": hundred,
            "R8690": hundred,
            "R9121": by_ten,
            "R9122": by_ten,
            "R9123": by_ten,
            "R9126": by_ten,
            "R9127": by_ten,
            "R9128": by_ten,
            "R9129": by_ten,
            "R16534": hundred,
            "R8002": ctwo_thousand,
            "R8005": ctwo_thousand,
            "R8008": ctwo_thousand,
            "R8011": ctwo_thousand,
            "R8105": ctwo,
            "R8110": ctwo,
            "R8111": thousand,
            "R8112": thousand,
            "R8220": thousand,
            "R8221": thousand,
            "R8222": thousand,
            "R8223": thousand,
        }.get(self._input.code, lambda v: v)(value)

    @property
    def binary_sensor_normalized_value(self) -> bool | None:
        """Get the normalized binary sensor value.

        Returns:
            Boolean value representing the sensor state.
        """
        value = self.value
        if value is None:
            return None
        if self.binary_sensor_device_class == BinarySensorDeviceClass.COLD:
            return not bool(value)
        return bool(value)

    @property
    def sensor_normalized_value(self) -> Any:
        """Get the normalized sensor value with unit conversions applied.

        Returns:
            The sensor value with appropriate scaling and unit conversions.
        """
        return self._scaled_value

    @property
    def switch_normalized_value(self) -> bool | None:
        """Get the normalized switch value.

        Returns:
            Boolean value representing the switch state.
        """
        value = self.value
        if value is None:
            return None
        return bool(self.value)

    @property
    def number_normalized_value(self) -> Any:
        """Get the normalized number value with unit conversions applied.

        Returns:
            The number value with appropriate scaling and unit conversions.
        """
        return self._scaled_value

    @cached_property
    def value_type(self) -> type:
        """Determine the Python type for this input's value.

        Returns:
            The type to use when converting raw Febos values (int, float, bool, or str).
        """
        if self._input.code in ["R8648", "R8967", "R9071", "R9072", "R9076", "R9078", "R9079"]:
            return bool
        return {
            "INT": int,
            "FLOAT": float,
            "BOOL": bool,
            "STRING": str,
        }[self._input.inputType]

    @cached_property
    def measurement_unit(self) -> str:
        """Get the Home Assistant unit of measurement for this input.

        Returns:
            Home Assistant unit constant (e.g., PERCENTAGE, UnitOfPower.WATT).

        Raises:
            ValueError: If measurement unit cannot be determined.
        """
        mu = {
            "CT_UPTIME": UnitOfTime.HOURS, # Uptime
            "R16494": UnitOfTemperature.CELSIUS,  # Set temp. della prima richiesta ACS
            "R16495": UnitOfTemperature.CELSIUS,  # Set temp. della seconda richiesta ACS
            "R16496": UnitOfTemperature.CELSIUS,  # Set temp. della seconda richiesta ACS
            "R16497": UnitOfTemperature.CELSIUS,  # Set temp. di mantenimento ACS
            "R16515": UnitOfTemperature.CELSIUS,  # Set di Rugiada/Umidita
            "R8680": UnitOfTemperature.CELSIUS,  # DWP
            "R8002": UnitOfPower.KILO_WATT,  # Potenza media DIE1
            "R8005": UnitOfPower.KILO_WATT,  # Potenza media DIE2
            "R8008": UnitOfPower.KILO_WATT,  # Potenza media DIE3
            "R8011": UnitOfPower.KILO_WATT,  # Potenza media DIE4
            "R8100": UnitOfElectricPotential.VOLT,  # Tensione TAE1
            "R8105": UnitOfPower.WATT,  # Potenza attiva TAE1
            "R8110": UnitOfPower.WATT,  # Potenza attiva TAE2
            "R8111": UnitOfElectricCurrent.AMPERE,  # Corrente TAE1
            "R8112": UnitOfElectricCurrent.AMPERE,  # Corrente TAE2
            "R8113": UnitOfFrequency.HERTZ,  # Sfasamento TAE1
            "R8114": UnitOfFrequency.HERTZ,  # Sfasamento TAE2
            "R8203": UnitOfTemperature.CELSIUS, # Offset sonda NTC1
            "R8204": UnitOfTemperature.CELSIUS, # Offset sonda NTC2
            "R8208": UnitOfTime.MILLISECONDS, # Minima durata impulso contatore HP
            "R8209": UnitOfTime.MILLISECONDS, # Massima durata impulso contatore HP
            "R8211": UnitOfTime.MILLISECONDS, # Minima durata impulso contatore Presa
            "R8212": UnitOfTime.MILLISECONDS, # Massima durata impulso contatore Presa
            "R8214": UnitOfTime.MILLISECONDS, # Minima durata impulso contatore FV
            "R8215": UnitOfTime.MILLISECONDS, # Massima durata impulso contatore FV
            "R8217": UnitOfTime.MILLISECONDS, # Minima durata impulso contatore Casa
            "R8218": UnitOfTime.MILLISECONDS, # Massima durata impulso contatore Casa
            "R8400": UnitOfElectricPotential.VOLT,  # Calibrazione tensione CH1
            "R8401": UnitOfElectricCurrent.AMPERE,  # Calibrazione corrente CH1
            "R8402": UnitOfElectricCurrent.AMPERE,  # Calibrazione corrente CH2
            "R8403": UnitOfPower.WATT,  # Offset potenza attiva CH1
            "R8404": UnitOfPower.WATT,  # Offset potenza attiva CH2
            "R8405": UnitOfFrequency.HERTZ,  # Compensazione fase tensione CH1
            "R8406": UnitOfFrequency.HERTZ,  # Compensazione fase corrente CH1
            "R8407": UnitOfFrequency.HERTZ,  # Compensazione fase corrente CH2
            "R8660": PERCENTAGE,  # Set umidità estate (SetRh_E)
            "R8661": PERCENTAGE,  # Set umidità inverno (SetRh_I)
            "R8665": UnitOfPower.KILO_WATT,  # Massima potenza fornita
            "R8666": UnitOfPower.KILO_WATT,  # Potenza FV installata
            "R8756": UnitOfPower.KILO_WATT,  # Potenza prelevata dalla rete
            "R8757": UnitOfPower.KILO_WATT,  # Potenza immessa in rete
            "R8758": UnitOfPower.KILO_WATT,  # Potenza_Home
            "R8759": UnitOfPower.KILO_WATT,  # Potenza_FV
            "R8760": UnitOfPower.KILO_WATT,  # Potenza_PDC
            "R8761": UnitOfPower.KILO_WATT,  # Potenza_Acs
            "R8762": UnitOfPower.KILO_WATT,  # Potenza_Presa1
            "R8763": UnitOfPower.KILO_WATT,  # Potenza_Risc_Pdc
            "R8764": UnitOfPower.KILO_WATT,  # Potenza_Raff_Pdc
            "R8765": UnitOfEnergy.WATT_HOUR,  # Energia prelevata dalla rete
            "R8766": UnitOfEnergy.WATT_HOUR,  # Energia immessa in rete
            "R8767": UnitOfEnergy.WATT_HOUR,  # Energia_Home
            "R8768": UnitOfEnergy.WATT_HOUR,  # Energia_FV
            "R8769": UnitOfEnergy.WATT_HOUR,  # Energia_PdC
            "R8770": UnitOfEnergy.WATT_HOUR,  # Energia_ACS
            "R8771": UnitOfEnergy.WATT_HOUR,  # Energia_Presa
            "R8772": UnitOfEnergy.WATT_HOUR,  # Energia_Risc_Pdc
            "R8773": UnitOfEnergy.WATT_HOUR,  # Energia_Raff_Pdc
            "R9042": UnitOfTemperature.CELSIUS,  # Temperatura minima acqua Radiante
            "R9051": UnitOfTemperature.CELSIUS,  # Temperatura attuale Acqua PdC
            "R9052": UnitOfTemperature.CELSIUS,  # Set temperatura Acqua PdC
            "R9120": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
            "R9121": UnitOfPower.WATT,
            "R9122": UnitOfPower.WATT,
            "R9123": UnitOfPower.WATT,
            "R9126": UnitOfPower.WATT,
            "R9127": UnitOfPower.WATT,
            "R9128": UnitOfPower.WATT,
            "R9129": UnitOfPower.WATT,
            "R16493": UnitOfTime.MINUTES
        }.get(self._input.code, self._input.measUnit)
        mu = mu if mu else ""
        mu = {
            "HH:mm": UnitOfTime.MINUTES,
            "watt/h": UnitOfEnergy.WATT_HOUR,
            "e/kw": CURRENCY_EURO,
        }.get(mu, mu)
        return mu

    @cached_property
    def label(self) -> str:
        """Get the display label for this input.

        Returns:
            Cleaned up label string for use as entity name.

        Raises:
            ValueError: If label is invalid or empty.
        """
        name = (
            self._input.name.replace(" (in KW)", "")
            .replace("(la tensione è unica per i due canali)", "")
            .replace("Pdc", "PdC")
            .replace("PcD", "PdC")
            .replace("PDC", "PdC")
            .replace("Acs", "ACS")
            .replace("Risc_", "Riscaldamento ")
            .replace("Raff_", "Raffreddamento ")
            .replace("Home", "Casa")
            .replace("(SetRh_E)", "")
            .replace("(SetRh_I)", "")
            .replace("On/ Off", "On/Off")
            .replace("CASA", "Casa")
            .replace("PRESA", "Presa")
            .replace("Presa1", "Presa")
            .replace("not used", "Non utilizzato")
            .replace("_", " ")
            .strip()
        )
        if not name:
            name = "Sconosciuto"
        return f"{self._input.code}: {name}"

    @cached_property
    def binary_sensor_device_class(self) -> BinarySensorDeviceClass:
        """Get the binary sensor device class for this input.

        Returns:
            BinarySensorDeviceClass constant matching this input's purpose.
        """
        return {
            "R8648": BinarySensorDeviceClass.COLD,
            "R8683": BinarySensorDeviceClass.COLD,
            "R8684": BinarySensorDeviceClass.COLD,
            "R16385": BinarySensorDeviceClass.COLD,
            "R9089": BinarySensorDeviceClass.PROBLEM,
            "R9090": BinarySensorDeviceClass.PROBLEM,
            "R9095": BinarySensorDeviceClass.PROBLEM,
            "R9096": BinarySensorDeviceClass.PROBLEM,
            "R9097": BinarySensorDeviceClass.PROBLEM,
            "R9098": BinarySensorDeviceClass.PROBLEM,
            "R9099": BinarySensorDeviceClass.PROBLEM,
            "R9102": BinarySensorDeviceClass.PROBLEM,
            "R9103": BinarySensorDeviceClass.PROBLEM,
            "R9104": BinarySensorDeviceClass.PROBLEM,
            "R16384": BinarySensorDeviceClass.RUNNING,
            "R8681": BinarySensorDeviceClass.RUNNING,
            "R8682": BinarySensorDeviceClass.RUNNING,
            "R8692": BinarySensorDeviceClass.RUNNING,
            "R8967": BinarySensorDeviceClass.RUNNING,
            "R9071": BinarySensorDeviceClass.RUNNING,
            "R9072": BinarySensorDeviceClass.RUNNING,
            "R9073": BinarySensorDeviceClass.RUNNING,
            "R9074": BinarySensorDeviceClass.RUNNING,
            "R9076": BinarySensorDeviceClass.RUNNING,
            "R9078": BinarySensorDeviceClass.RUNNING,
            "R9079": BinarySensorDeviceClass.RUNNING,
            "R8672": BinarySensorDeviceClass.WINDOW,
            "R8673": BinarySensorDeviceClass.PRESENCE,
            "R8676": BinarySensorDeviceClass.PRESENCE,
        }[self._input.code]

    @cached_property
    def sensor_device_class(self) -> SensorDeviceClass | None:
        """Get the sensor device class based on measurement unit.

        Returns:
            SensorDeviceClass constant matching this input's measurement unit.

        Raises:
            ValueError: If no valid device class is found for the measurement unit.
        """
        mu = self.measurement_unit
        if not mu:
            return None
        if mu == PERCENTAGE:
            return SensorDeviceClass.HUMIDITY
        if mu == CURRENCY_EURO:
            return SensorDeviceClass.MONETARY
        if mu in UnitOfPower:
            return SensorDeviceClass.POWER
        if mu in UnitOfTemperature:
            return SensorDeviceClass.TEMPERATURE
        if mu in UnitOfTime:
            return SensorDeviceClass.DURATION
        if mu in UnitOfEnergy:
            return SensorDeviceClass.ENERGY
        if mu in UnitOfFrequency:
            return SensorDeviceClass.FREQUENCY
        if mu in UnitOfElectricPotential:
            return SensorDeviceClass.VOLTAGE
        if mu in UnitOfElectricCurrent:
            return SensorDeviceClass.CURRENT
        if mu in UnitOfVolumeFlowRate:
            return SensorDeviceClass.VOLUME_FLOW_RATE
        LOGGER.error(f"Invalid input: {self._input}")
        raise ValueError(f"Invalid measurement unit '{mu}' for '{self._input.code}'.")

    @cached_property
    def switch_device_class(self) -> SwitchDeviceClass | None:
        """Get the switch device class.

        Returns:
            SwitchDeviceClass constant matching this switch device class.
        """
        return SwitchDeviceClass.SWITCH

    @cached_property
    def number_device_class(self) -> NumberDeviceClass | None:
        """Get the number device class based on measurement unit.

        Returns:
            NumberDeviceClass constant matching this input's measurement unit.

        Raises:
            ValueError: If no valid device class is found for the measurement unit.
        """
        mu = self.measurement_unit
        if not mu:
            return None
        if mu == PERCENTAGE:
            return NumberDeviceClass.HUMIDITY
        if mu == CURRENCY_EURO:
            return NumberDeviceClass.MONETARY
        if mu in UnitOfPower:
            return NumberDeviceClass.POWER
        if mu in UnitOfTemperature:
            return NumberDeviceClass.TEMPERATURE
        if mu in UnitOfTime:
            return NumberDeviceClass.DURATION
        if mu in UnitOfEnergy:
            return NumberDeviceClass.ENERGY
        if mu in UnitOfFrequency:
            return NumberDeviceClass.FREQUENCY
        if mu in UnitOfElectricPotential:
            return NumberDeviceClass.VOLTAGE
        if mu in UnitOfElectricCurrent:
            return NumberDeviceClass.CURRENT
        if mu in UnitOfVolumeFlowRate:
            return NumberDeviceClass.VOLUME_FLOW_RATE
        LOGGER.error(f"Invalid input: {self._input}")
        raise ValueError(f"Invalid measurement unit '{mu}' for '{self._input.code}'.")

    @cached_property
    def sensor_state_class(self) -> SensorStateClass | None:
        """Get the sensor state class based on device class.

        Returns:
            SensorStateClass constant (MEASUREMENT or TOTAL).

        Raises:
            ValueError: If no valid state class is found.
        """
        sscls = SensorStateClass.MEASUREMENT
        scls = self.sensor_device_class
        if scls:
            sscls = {
                SensorDeviceClass.MONETARY: SensorStateClass.TOTAL,
                SensorDeviceClass.POWER: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.TEMPERATURE: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.DURATION: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.FREQUENCY: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.VOLTAGE: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.CURRENT: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.ENERGY: SensorStateClass.TOTAL,
                SensorDeviceClass.VOLUME_FLOW_RATE: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.HUMIDITY: SensorStateClass.MEASUREMENT,
                SensorDeviceClass.ENUM: SensorStateClass.MEASUREMENT,
            }.get(scls)
        return sscls

    @cached_property
    def entity_type(self) -> Platform:
        """Determine the entity type of this input.

        Returns:
            The entity type of this input as a Platform enum.

        Raises:
            ValueError: If entity type cannot be determined.
        """
        force_read_only = (self.thing_model_id == 8 or self.code in ["R8681", "R8682", "R16515"])
        value_type = self.value_type
        if self._input.category == "C_PARAMETER" and not force_read_only:
            return {
                bool: Platform.SWITCH,
                float: Platform.NUMBER,
                int: Platform.NUMBER,
            }[value_type]
        elif self._input.category == "C_DATA" or force_read_only:
            if value_type is bool:
                return Platform.BINARY_SENSOR
            else:
                return Platform.SENSOR
        else:
            raise ValueError(f"Unknown input category '{self._input.category}'")

    @property
    def normalized_value(self) -> Any:
        """Get the normalized value.

        Returns:
            Value representing the entity state.
        """
        if self.entity_type == Platform.BINARY_SENSOR:
            return self.binary_sensor_normalized_value
        if self.entity_type == Platform.SENSOR:
            return self.sensor_normalized_value
        if self.entity_type == Platform.SWITCH:
            return self.switch_normalized_value
        if self.entity_type == Platform.NUMBER:
            return self.number_normalized_value
        raise ValueError(f"Unsupported entity type '{self.entity_type}'")
