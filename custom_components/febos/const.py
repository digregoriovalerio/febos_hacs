"""EmmeTI Febos Constants."""

import logging

from homeassistant.const import Platform

DOMAIN = "febos"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]

LOGGER = logging.getLogger(__package__)
