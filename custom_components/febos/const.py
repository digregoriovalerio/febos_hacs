"""EmmeTI Febos Constants."""

import logging

from homeassistant.const import Platform

DOMAIN = "febos"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

LOGGER = logging.getLogger(__package__)
FORMAT = "[%(filename)s:%(lineno)s] [%(funcName)s()] %(message)s"
logging.basicConfig(format=FORMAT)
LOGGER.setLevel(logging.DEBUG)
