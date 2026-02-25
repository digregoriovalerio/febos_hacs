"""EmmeTI Febos API."""

from typing import Any

from febos import FebosClient, LoginEndpoint, PageConfigEndpoint, RealtimeDataEndpoint, Value
from febos.realtime_data import RealtimeDataModel
from homeassistant.const import Platform
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from httpx import HTTPStatusError

from .const import DOMAIN, LOGGER
from .normalization import NormalizedInput


def unique_key(
    installation_id: int,
    device_id: int,
    thing_id: int,
    input_code: str | None = None,
    domain: str | None = None,
) -> str:
    """Concatenate a list of parameters into a unique key format."""
    parts = []
    if domain:
        parts.append(domain)
    parts.append(str(installation_id))
    parts.append(str(device_id))
    parts.append(str(thing_id))
    if input_code:
        parts.append(input_code)
    return "_".join(parts)


class FebosSession:
    """Manage Febos API session and device discovery."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize a Febos session.

        Args:
            username: Username for Febos API authentication.
            password: Password for Febos API authentication.
        """
        self.client = FebosClient()
        self.username = username
        self.password = password
        self.installations: list[int] = []
        self.groups: dict[int, list[str]] = {}
        self.devices: dict[int, dict[int, dict[int, DeviceInfo]]] = {}
        self.inputs: dict[int, dict[int, dict[int, dict[str, NormalizedInput]]]] = {}
        self.inputs_map: dict[str, NormalizedInput] = {}
        LOGGER.debug(f"Created session for user '{self.username}'")

    def _entities(self, entity_type: Platform) -> list[NormalizedInput]:
        """Get all entities with a given entity type.

        Returns:
            List of NormalizedInput objects representing the requested entities.
        """
        return [
            x
            for d in self.inputs.values()
            for t in d.values()
            for i in t.values()
            for x in i.values()
            if x.entity_type == entity_type
        ]

    @property
    def binary_sensors(self) -> list[NormalizedInput]:
        """Get all binary sensors from the Febos installation.

        Returns:
            List of NormalizedInput objects representing binary sensor entities.
        """
        return self._entities(Platform.BINARY_SENSOR)

    @property
    def sensors(self) -> list[NormalizedInput]:
        """Get all sensors from the Febos installation.

        Returns:
            List of NormalizedInput objects representing sensor entities.
        """
        return self._entities(Platform.SENSOR)

    @property
    def switches(self) -> list[NormalizedInput]:
        """Get all switches from the Febos installation.

        Returns:
            List of NormalizedInput objects representing switch entities.
        """
        return self._entities(Platform.SWITCH)

    @property
    def numbers(self) -> list[NormalizedInput]:
        """Get all numbers from the Febos installation.

        Returns:
            List of NormalizedInput objects representing number entities.
        """
        return self._entities(Platform.NUMBER)

    def login(self) -> None:
        """Authenticate with the Febos API and retrieve installation IDs.

        Raises:
            Exception: If authentication fails.
        """
        login = LoginEndpoint(username=self.username, password=self.password)
        response = login.post(self.client)
        self.installations: list[int] = response.installationIdList
        LOGGER.debug(f"Login successful for user '{self.username}'")
        LOGGER.debug(f"Found {len(self.installations)} installations: '{', '.join(str(i) for i in self.installations)}'")

    def discover(self):
        """Discover devices and resources from Febos webapp."""
        groups: dict[int, set[str]] = {}
        devices: dict[int, dict[int, dict[int, DeviceInfo]]] = {}
        inputs: dict[int, dict[int, dict[int, dict[str, NormalizedInput]]]] = {}
        
        for installation_id in self.installations:
            devices[installation_id] = {}
            groups[installation_id] = set()
            inputs[installation_id] = {}

            LOGGER.debug(f"Device discovery started for installation {installation_id}")

            page_config = PageConfigEndpoint(installation_id=installation_id)
            response = page_config.get(self.client)

            for thing in response.thingMap.values():
                LOGGER.debug(f"Found thing: {thing.name} ({thing.id})")
                if thing.deviceId not in devices[installation_id]:
                    devices[installation_id][thing.deviceId] = {}
                if thing.id not in devices[installation_id][thing.deviceId]:
                    device = response.deviceMap[str(thing.deviceId)]
                    LOGGER.debug(f"This thing belongs to device: {device.name} ({device.id})")
                    devices[installation_id][thing.deviceId][thing.id] = DeviceInfo(
                        identifiers={
                            (
                                DOMAIN,
                                unique_key(
                                    installation_id,
                                    thing.deviceId,
                                    thing.id,
                                ),
                            )
                        },
                        entry_type=DeviceEntryType.SERVICE,
                        manufacturer=device.tenantName,
                        model=f"{device.code}: {device.modelName}",
                        name=f"{thing.modelCode}-{thing.id}: {thing.modelName}",
                    )

            for page in response.pageMap.values():
                groups[installation_id].update(page.inputGroupGetCodeList)
                for tab in page.tabList:
                    for map in tab.inputGroupGetCodeMap.values():
                        groups[installation_id].update(map)
                    for widget in tab.widgetList:
                        groups[installation_id].update(widget.inputGroupGetCodeList)
                        for group in widget.widgetInputGroupList:
                            groups[installation_id].add(group.inputGroupGetCode)
                            for input_entry in group.inputList:
                                if input_entry.deviceId not in inputs[installation_id]:
                                    inputs[installation_id][input_entry.deviceId] = {}
                                if (
                                    input_entry.thingId
                                    not in inputs[installation_id][input_entry.deviceId]
                                ):
                                    inputs[installation_id][input_entry.deviceId][
                                        input_entry.thingId
                                    ] = {}
                                if (
                                    input_entry.code
                                    in inputs[installation_id][input_entry.deviceId][
                                        input_entry.thingId
                                    ]
                                ):
                                    continue

                                device_info = (
                                    devices.get(installation_id, {})
                                    .get(input_entry.deviceId, {})
                                    .get(input_entry.thingId, None)
                                )
                                if not device_info:
                                    raise ValueError(
                                        f"Device not found for input: installation_id={installation_id}, device_id={input_entry.deviceId}, thing_id={input_entry.thingId}."
                                    )

                                LOGGER.debug(
                                    f"Found: {input_entry.code} - {input_entry.name} @ D{input_entry.deviceId}/T{input_entry.thingId}"
                                )

                                thing = response.thingMap[str(input_entry.thingId)]

                                inputs[installation_id][input_entry.deviceId][
                                    input_entry.thingId
                                ][input_entry.code] = NormalizedInput(
                                    key=unique_key(
                                        installation_id,
                                        input_entry.deviceId,
                                        input_entry.thingId,
                                        input_entry.code,
                                        DOMAIN,
                                    ),
                                    installation_id=installation_id,
                                    thing_model_id=thing.modelId,
                                    device_info=device_info,
                                    input_entry=input_entry,
                                )

                LOGGER.debug(f"Groups: {', '.join(groups[installation_id])}")

        self.groups = {k: list(v) for k, v in groups.items()}
        self.devices = devices
        self.inputs = inputs
        self.inputs_map = {
            x.key: x
            for d in self.inputs.values()
            for t in d.values()
            for i in t.values()
            for x in i.values()
        }

    def update(self) -> dict[str, Any]:
        """Update values from Febos webapp.

        Fetches realtime data for all devices and input groups and updates
        the corresponding NormalizedInput objects with new values.

        Returns:
            Dictionary mapping unique keys to NormalizedInput objects.
        """
        for installation_id in self.installations:
            realtime_data = RealtimeDataEndpoint(
                installation_id=installation_id,
                input_group_list=self.groups[installation_id],
            )
            realtime_data_response = realtime_data.get(self.client)
            for entry in realtime_data_response.root:
                for code, value in entry.data.items():
                    input_entry = (
                        self.inputs.get(installation_id, {})
                        .get(entry.deviceId, {})
                        .get(entry.thingId, {})
                        .get(code)
                    )
                    if input_entry:
                        input_entry.value = value.i
                    else:
                        LOGGER.warning(
                            f"Received value '{value.i}' for unknown input: installation_id={installation_id}, device_id={entry.deviceId}, thing_id={entry.thingId}, code={code}"
                        )
        return {
            x.key: x.normalized_value
            for d in self.inputs.values()
            for t in d.values()
            for i in t.values()
            for x in i.values()
        }

    def set_value(self, key: str, value: Any) -> dict[str, Any] | None:
        LOGGER.debug(f"Setting value {value} for {key}")

        if key not in self.inputs_map:
            LOGGER.warning(f"Cannot set value for unknown key '{key}'")
            return None

        input = self.inputs_map[key]
        value = input.to_original_scale(value)
        realtime_data = RealtimeDataEndpoint(
            installation_id=input.installation_id,
            input_group_list=self.groups[input.installation_id],
        )
        data = RealtimeDataModel(
            data={input.code: Value(i=value)},
            deviceId=input.device_id,
            thingId=input.thing_id,
        )

        try:
            realtime_data_response = realtime_data.post(self.client, data)
        except HTTPStatusError as e:
            LOGGER.warning(f"Value update failed due to remote error: {e}. {e.response}")
            return None

        if realtime_data_response.errCode != 0:
            LOGGER.warning(f"Value update failed due to remote error: {realtime_data_response.msg} (error code: {realtime_data_response.errCode})")
            return None

        input.value = value

        return {
            x.key: x.normalized_value
            for d in self.inputs.values()
            for t in d.values()
            for i in t.values()
            for x in i.values()
        }