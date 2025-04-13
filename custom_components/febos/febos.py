"""EmmeTI Febos helpers for Home Assistant integration."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from febos.api import Device, FebosApi, Input, Slave, Thing
from febos.errors import AuthenticationError
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CURRENCY_EURO,
    PERCENTAGE,
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, LOGGER


def unique_key(*args) -> str:
    """Concatenate a list of parameters into a unique key format."""
    return "_".join(
        str(a).replace("_", "").replace("-", "").lower() for a in (DOMAIN, *args)
    )


def int16(v):
    """Convert a two's complement 16-bits integer into an int."""
    v = int(v)
    return v if v < 32768 else v - 65536


IGNORED_RESOURCES = [
    "R8205",
    "R8206",
    "R8207",
]

OVERRIDE_MEASUREMENT_UNIT_MAP = {
    "CT_UPTIME": "",  # Uptime
    "CT_VPN_IP": "",  # OpenVPN IP Address
    "R16493": "",  # Orario della prima richiesta ACS
    "R16494": "°C",  # Set temp. della prima richiesta ACS
    "R16495": "°C",  # Set temp. della seconda richiesta ACS
    "R16496": "°C",  # Set temp. della seconda richiesta ACS
    "R16497": "°C",  # Set temp. di mantenimento ACS
    "R16515": "°C",  # Set di Rugiada/Umidita
    "R8002": "kW",  # Potenza media DIE1
    "R8005": "kW",  # Potenza media DIE2
    "R8008": "kW",  # Potenza media DIE3
    "R8011": "kW",  # Potenza media DIE4
    "R8100": "V",  # Tensione TAE1
    "R8105": "kW",  # Potenza attiva TAE1
    "R8110": "kW",  # Potenza attiva TAE2
    "R8111": "A",  # Corrente TAE1
    "R8112": "A",  # Corrente TAE2
    "R8113": "",  # Sfasamento TAE1
    "R8114": "",  # Sfasamento TAE2
    "R8200": "",  # Superparametro 1
    "R8201": "",  # Superparametro 2
    "R8202": "",  # Superparametro 3
    "R8203": "",  # Offset sonda NTC1
    "R8204": "",  # Offset sonda NTC2
    "R8205": "",  # not used
    "R8206": "",  # not used
    "R8207": "",  # not used
    "R8208": "",  # Minima durata impulso contatore HP
    "R8209": "",  # Massima durata impulso contatore HP
    "R8210": "",  # Valore corrispondente ad 1 impulso
    "R8211": "",  # Minima durata impulso contatore Presa
    "R8212": "",  # Massima durata impulso contatore Presa
    "R8213": "",  # Valore corrispondente ad 1 impulso
    "R8214": "",  # Minima durata impulso contatore FV
    "R8215": "",  # Massima durata impulso contatore FV
    "R8216": "",  # Valore corrispondente ad 1 impulso
    "R8217": "",  # Minima durata impulso contatore Casa
    "R8218": "",  # Massima durata impulso contatore Casa
    "R8219": "",  # Valore corrispondente ad 1 impulso
    "R8300": "",  # N. impulsi scartati perchè corti FV
    "R8301": "",  # N. impulsi scartati perchè lunghi FV
    "R8302": "",  # N. impulsi scartati perchè troppo vicini FV
    "R8303": "",  # N. impulsi scartati perchè corti CASA
    "R8304": "",  # N. impulsi scartati perchè lunghi CASA
    "R8305": "",  # N. impulsi scartati perchè troppo vicini CASA
    "R8306": "",  # N. impulsi scartati perchè corti HP
    "R8307": "",  # N. impulsi scartati perchè lunghi HP
    "R8308": "",  # N. impulsi scartati perchè troppo vicini HP
    "R8309": "",  # N. impulsi scartati perchè corti PRESA
    "R8310": "",  # N. impulsi scartati perchè lunghi PRESA
    "R8311": "",  # N. impulsi scartati perchè troppo vicini PRESA
    "R8400": "",  # Calibrazione tensione CH1
    "R8401": "",  # Calibrazione corrente CH1
    "R8402": "",  # Calibrazione corrente CH2
    "R8403": "",  # Offset potenza attiva CH1
    "R8404": "",  # Offset potenza attiva CH2
    "R8405": "",  # Compensazione fase tensione CH1
    "R8406": "",  # Compensazione fase corrente CH1
    "R8407": "",  # Compensazione fase corrente CH2
    "R8408": "",  # Contenuto del registro di taratura della tensione CH1
    "R8409": "",  # Contenuto del registro di taratura della corrente CH1 (Word più significativa)
    "R8410": "",  # Contenuto del registro di taratura della corrente CH1 (Word meno significativa)
    "R8411": "",  # Contenuto del registro di taratura della corrente CH2 (Word più significativa)
    "R8412": "",  # Contenuto del registro di taratura della corrente CH2 (Word meno significativa)
    "R8413": "",  # Contenuto del registro di taratura dello sfasamento relativo a CH1
    "R8414": "",  # Contenuto del registro di taratura dello sfasamento relativo a CH2
    "R8600": "",  # Data produzione (parte alta)
    "R8638": "",  # Configurazione potenze 1
    "R8639": "",  # Configurazione potenze 2
    "R8640": "",  # Configurazione potenze 3
    "R8641": "",  # Configurazione potenze 4
    "R8642": "",  # Configurazione potenze 5
    "R8660": "%",  # Set umidità estate (SetRh_E)
    "R8661": "%",  # Set umidità inverno (SetRh_I)
    "R8664": "",  # Nome Febos Crono
    "R8665": "kW",  # Massima potenza fornita
    "R8666": "kW",  # Potenza FV installata
    "R8756": "kW",  # Potenza prelevata dalla rete
    "R8757": "kW",  # Potenza immessa in rete
    "R8758": "kW",  # Potenza_Home
    "R8759": "kW",  # Potenza_FV
    "R8760": "kW",  # Potenza_PDC
    "R8761": "kW",  # Potenza_Acs
    "R8762": "kW",  # Potenza_Presa1
    "R8763": "kW",  # Potenza_Risc_Pdc
    "R8764": "kW",  # Potenza_Raff_Pdc
    "R8765": "watt/h",  # Energia prelevata dalla rete
    "R8766": "watt/h",  # Energia immessa in rete
    "R8767": "watt/h",  # Energia_Home
    "R8768": "watt/h",  # Energia_FV
    "R8769": "watt/h",  # Energia_PdC
    "R8770": "watt/h",  # Energia_ACS
    "R8771": "watt/h",  # Energia_Presa
    "R8772": "watt/h",  # Energia_Risc_Pdc
    "R8773": "watt/h",  # Energia_Raff_Pdc
    "R8774": "",  # EER/COP
    "R9008": "",  # Step frequenza PdC
    "R9042": "°C",  # Temperatura minima acqua Radiante
    "R9051": "°C",  # Temperatura attuale Acqua PdC
    "R9052": "°C",  # Set temperatura Acqua PdC
}

MEASUREMENT_UNIT_MAP = {
    "kW": UnitOfPower.KILO_WATT,
    "V": UnitOfElectricPotential.VOLT,
    "A": UnitOfElectricCurrent.AMPERE,
    "°C": UnitOfTemperature.CELSIUS,
    "°": UnitOfTemperature.CELSIUS,
    "h": UnitOfTime.HOURS,
    "HH:mm": UnitOfTime.MINUTES,
    "watt/h": UnitOfEnergy.WATT_HOUR,
    "L/h": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    "e/kw": CURRENCY_EURO,
    "%": PERCENTAGE,
}

SENSOR_STATE_CLASS_MAP = {
    SensorDeviceClass.MONETARY: SensorStateClass.TOTAL,
    SensorDeviceClass.POWER: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.TEMPERATURE: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.DURATION: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.ENERGY: SensorStateClass.TOTAL,
    SensorDeviceClass.VOLUME_FLOW_RATE: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.HUMIDITY: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.ENUM: SensorStateClass.MEASUREMENT,
}

BINARY_SENSOR_DEVICE_CLASS_MAP = {
    "R8648": BinarySensorDeviceClass.COLD,
    "R8683": BinarySensorDeviceClass.COLD,
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
}

INPUT_TYPE_MAP = {
    "INT": int,
    "FLOAT": float,
    "BOOL": bool,
    "STRING": str,
}


SENSOR_VALUE_MAP = {
    "R9120": lambda v: float(v) * 60.0,
    "R8100": lambda v: float(v) / 10.0,
    "R8665": lambda v: float(v) / 10.0,
    "R8666": lambda v: float(v) / 10.0,
    "R8678": lambda v: float(v) / 10.0,
    "R8680": lambda v: float(v) / 10.0,
    "R8698": lambda v: float(v) / 10.0,
    "R8702": lambda v: float(v) / 10.0,
    "R8703": lambda v: float(v) / 10.0,
    "R8986": lambda v: float(v) / 10.0,
    "R8987": lambda v: float(v) / 10.0,
    "R8988": lambda v: float(v) / 10.0,
    "R8989": lambda v: float(v) / 10.0,
    "R9042": lambda v: float(v) / 10.0,
    "R9051": lambda v: float(v) / 10.0,
    "R9052": lambda v: float(v) / 10.0,
    "R16444": lambda v: float(v) / 10.0,
    "R16446": lambda v: float(v) / 10.0,
    "R16448": lambda v: float(v) / 10.0,
    "R16450": lambda v: float(v) / 10.0,
    "R16451": lambda v: float(v) / 10.0,
    "R16453": lambda v: float(v) / 10.0,
    "R16455": lambda v: float(v) / 10.0,
    "R16457": lambda v: float(v) / 10.0,
    "R16494": lambda v: float(v) / 10.0,
    "R16495": lambda v: float(v) / 10.0,
    "R16496": lambda v: float(v) / 10.0,
    "R16497": lambda v: float(v) / 10.0,
    "R16515": lambda v: float(v) / 10.0,
    "S04": lambda v: float(v) / 10.0,
    "S05": lambda v: float(v) / 10.0,
    "R8684": lambda v: float(v) / 100.0,
    "R8686": lambda v: float(v) / 100.0,
    "R8688": lambda v: float(v) / 100.0,
    "R8690": lambda v: float(v) / 100.0,
    "R9121": lambda v: float(v) / 100.0,
    "R9122": lambda v: float(v) / 100.0,
    "R9123": lambda v: float(v) / 100.0,
    "R9126": lambda v: float(v) / 100.0,
    "R9127": lambda v: float(v) / 100.0,
    "R9128": lambda v: float(v) / 100.0,
    "R9129": lambda v: float(v) / 100.0,
    "R16534": lambda v: float(v) / 100.0,
    "R8002": lambda v: float(int16(v)) / 1000.0,
    "R8005": lambda v: float(int16(v)) / 1000.0,
    "R8008": lambda v: float(int16(v)) / 1000.0,
    "R8011": lambda v: float(int16(v)) / 1000.0,
    "R8105": lambda v: float(int16(v)) / 1000.0,
    "R8110": lambda v: float(int16(v)) / 1000.0,
    "R8111": lambda v: float(v) / 1000.0,
    "R8112": lambda v: float(v) / 1000.0,
    "R8220": lambda v: float(v) / 1000.0,
    "R8221": lambda v: float(v) / 1000.0,
    "R8222": lambda v: float(v) / 1000.0,
    "R8223": lambda v: float(v) / 1000.0,
}

BINARY_SENSOR_VALUE_MAP = {
    BinarySensorDeviceClass.COLD: lambda v: not bool(v),
    BinarySensorDeviceClass.PRESENCE: lambda v: not bool(v),
    BinarySensorDeviceClass.HEAT: bool,
    BinarySensorDeviceClass.PROBLEM: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.RUNNING: bool,
    BinarySensorDeviceClass.WINDOW: bool,
}


@dataclass
class FebosResourceData:
    """Parsed EmmeTI Febos resource."""

    id: str
    name: str
    type: Platform
    sensor_class: BinarySensorDeviceClass | SensorDeviceClass
    value_type: type
    state_class: SensorStateClass = None
    meas_unit: str = None
    value: Any = None
    listener: Callable = None

    def set_value(self, value: Any) -> None:
        """Set current value."""
        old_value = self.value
        self.value = self.value_type(value)
        if self.listener is not None and old_value != self.value:
            self.listener()

    def get_value(self) -> Any:
        """Return current value."""
        if self.value is None:
            return None
        if self.type == Platform.SENSOR:
            return SENSOR_VALUE_MAP.get(self.id, lambda v: v)(self.value)
        if self.type == Platform.BINARY_SENSOR:
            return BINARY_SENSOR_VALUE_MAP[self.sensor_class](self.value)
        raise ValueError(self.type)

    def _parse_binary_sensor_value(self):
        """Normalize the binary sensor value."""
        if self.value is None:
            return None
        if self.sensor_class in [
            BinarySensorDeviceClass.COLD,
            BinarySensorDeviceClass.PRESENCE,
        ]:
            return not bool(self.value)
        return bool(self.value)

    @staticmethod
    def parse(resource: Input):
        """Parse an EmmeTI Febos resource."""

        def normalize_name(n):
            n = (
                n.replace(" (in KW)", "")
                .replace("PcD", "PdC")
                .replace(" (la tensione è unica per i due canali)", "")
            )
            if "R9127" in n:
                n = "R9127: Potenza Importata/Esportata"
            return n if len(n) > 0 else "Unknown"

        def normalize_sensor_class(u):
            if u == "":
                return None
            if u == PERCENTAGE:
                return SensorDeviceClass.HUMIDITY
            if u == CURRENCY_EURO:
                return SensorDeviceClass.MONETARY
            if u in UnitOfPower:
                return SensorDeviceClass.POWER
            if u in UnitOfTemperature:
                return SensorDeviceClass.TEMPERATURE
            if u in UnitOfTime:
                return SensorDeviceClass.DURATION
            if u in UnitOfEnergy:
                return SensorDeviceClass.ENERGY
            if u in UnitOfElectricPotential:
                return SensorDeviceClass.VOLTAGE
            if u in UnitOfElectricCurrent:
                return SensorDeviceClass.CURRENT
            if u in UnitOfVolumeFlowRate:
                return SensorDeviceClass.VOLUME_FLOW_RATE
            LOGGER.error(f"Unknown sensor class for {u!r}")
            raise ValueError(u)

        def normalize_measurement_unit(u, c):
            u = OVERRIDE_MEASUREMENT_UNIT_MAP.get(c, u)
            if u is None:
                LOGGER.error(f"Missing measurement unit in {c}")
                raise ValueError(c)
            return MEASUREMENT_UNIT_MAP.get(u, "")

        def parse_binary_sensor(n, c):
            clz = BINARY_SENSOR_DEVICE_CLASS_MAP[c]
            return FebosResourceData(
                id=c,
                name=n,
                type=Platform.BINARY_SENSOR,
                sensor_class=clz,
                value_type=bool,
            )

        def parse_sensor(n, c, u):
            u = normalize_measurement_unit(u, c)
            clz = normalize_sensor_class(u)
            return FebosResourceData(
                id=c,
                name=n,
                type=Platform.SENSOR,
                sensor_class=clz,
                state_class=SENSOR_STATE_CLASS_MAP.get(clz),
                meas_unit=u,
                value_type=value_type,
            )

        def parse_input_type(t, c):
            if c in BINARY_SENSOR_DEVICE_CLASS_MAP:
                return bool
            return INPUT_TYPE_MAP[t]

        name = normalize_name(resource.label)
        value_type = parse_input_type(resource.inputType, resource.code)
        if value_type is bool:
            return parse_binary_sensor(name, resource.code)
        if value_type in [int, float, str]:
            return parse_sensor(
                name, resource.code, getattr(resource, "measUnit", None)
            )
        raise ValueError(resource)


SLAVE_RESOURCES = {
    "callTemp": FebosResourceData(
        id="S01",
        name="S01: Chiamata Temperatura",
        type=Platform.BINARY_SENSOR,
        sensor_class=BinarySensorDeviceClass.HEAT,
        value_type=bool,
    ),
    "callHumid": FebosResourceData(
        id="S02",
        name="S02: Chiamata Umidità",
        type=Platform.BINARY_SENSOR,
        sensor_class=BinarySensorDeviceClass.HEAT,
        value_type=bool,
    ),
    "stagione": FebosResourceData(
        id="S03",
        name="S03: Stagione",
        type=Platform.BINARY_SENSOR,
        sensor_class=BinarySensorDeviceClass.COLD,
        value_type=bool,
    ),
    "setTemp": FebosResourceData(
        id="S04",
        name="S04: Set Temperatura",
        type=Platform.SENSOR,
        sensor_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        meas_unit=UnitOfTemperature.CELSIUS,
        value_type=float,
    ),
    "temp": FebosResourceData(
        id="S05",
        name="S05: Temperatura",
        type=Platform.SENSOR,
        sensor_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        meas_unit=UnitOfTemperature.CELSIUS,
        value_type=float,
    ),
    "humid": FebosResourceData(
        id="S06",
        name="S06: Umidità",
        type=Platform.SENSOR,
        sensor_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        meas_unit=PERCENTAGE,
        value_type=float,
    ),
    "confort": FebosResourceData(
        id="S07",
        name="S07: Comfort",
        type=Platform.BINARY_SENSOR,
        sensor_class=BinarySensorDeviceClass.PRESENCE,
        value_type=bool,
    ),
}


class FebosClient:
    """EmmeTI Febos client."""

    def __init__(self, api: FebosApi) -> None:
        """Initialize a client."""
        self.api = api
        self.groups = set()
        self.installations = []
        self.devices = {}
        self.resources = {}
        self.services = {}

    def add_service(self, device: Device, service: Thing | Slave) -> None:
        """Add a service for a given device and thing or slave."""
        if type(service) is Slave:
            service_id = service.indirizzoSlave
            service_name = f"{device.modelName} Slave {service.indirizzoSlave}"
        else:
            service_id = service.id
            service_name = service.modelName
        key = unique_key(device.installationId, device.id, service_id)
        if key not in self.services:
            self.services[key] = DeviceInfo(
                identifiers={(DOMAIN, device.installationId, device.id, service_id)},
                entry_type=DeviceEntryType.SERVICE,
                manufacturer=device.tenantName,
                model=device.modelName,
                name=service_name,
            )

    def set_value(self, key: str, value: Any) -> None:
        """Handle value update of a resource."""
        if key in self.resources:
            self.resources[key].set_value(value)
        else:
            LOGGER.warning(f"Resource not found: {key}")

    def discover(self):
        """Discover services and resource from the Febos webapp."""

        def discover_slaves(i, d):
            get_febos_slave = self.api.get_febos_slave(i, d.id)
            for slave in get_febos_slave:
                self.add_service(d, slave)
                for k in slave.__dict__:
                    if k in SLAVE_RESOURCES:
                        self.resources[
                            unique_key(
                                i,
                                d.id,
                                slave.indirizzoSlave,
                                k,
                            )
                        ] = deepcopy(SLAVE_RESOURCES[k])

        def discover_device(i, d):
            self.devices[d.id] = d
            discover_slaves(i, d)

        def discover_thing(t, d):
            if t.deviceId in self.devices:
                self.add_service(self.devices[t.deviceId], t)
            else:
                LOGGER.warning(f"Device not found: {t.deviceId}")

        def discover_resource(r):
            if r.code not in IGNORED_RESOURCES:
                self.resources[
                    unique_key(
                        installation_id,
                        r.deviceId,
                        r.thingId,
                        r.code,
                    )
                ] = FebosResourceData.parse(r)

        def discover_group(g):
            self.groups.add(g.inputGroupGetCode)
            for resource in g.inputList:
                assert resource.deviceId == device.id
                discover_resource(resource)

        def list_groups(m):
            for page in m.values():
                for tab in page.tabList:
                    for widget in tab.widgetList:
                        yield from widget.widgetInputGroupList

        login = self.api.login()
        self.installations = login.installationIdList
        for installation_id in self.installations:
            page_config = self.api.page_config(installation_id)
            for device in page_config.deviceMap.values():
                discover_device(installation_id, device)
                for thing in page_config.thingMap.values():
                    discover_thing(thing, device)
                for group in list_groups(page_config.pageMap):
                    discover_group(group)
        LOGGER.debug(f"Loaded {len(self.resources)} resources.")

    def do_update(self):
        """Update values from Febos webapp."""
        for installation_id in self.installations:
            realtime_data = self.api.realtime_data(installation_id, self.groups)
            for entry in realtime_data:
                for code, value in entry.data.items():
                    if code not in IGNORED_RESOURCES:
                        self.set_value(
                            unique_key(
                                installation_id, entry.deviceId, entry.thingId, code
                            ),
                            value.i,
                        )
            for device_id in self.devices:
                get_febos_slave = self.api.get_febos_slave(installation_id, device_id)
                for slave in get_febos_slave:
                    for k in slave.__dict__:
                        if k in SLAVE_RESOURCES:
                            self.set_value(
                                unique_key(
                                    installation_id,
                                    device_id,
                                    slave.indirizzoSlave,
                                    k,
                                ),
                                getattr(slave, k),
                            )

    def update(self) -> dict[str, Any]:
        """Update values from Febos webapp and retry login in case of session timeout."""
        try:
            self.do_update()
        except AuthenticationError as e:
            LOGGER.debug(f"Session timed out. {e}")
            self.api.login()
            LOGGER.debug("Logged in")
            self.do_update()
        return self.resources
