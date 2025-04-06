"""EmmeTI Febos data update coordinator."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER
from .febos import FebosClient

type FebosConfigEntry = ConfigEntry[FebosDataUpdateCoordinator]


class FebosDataUpdateCoordinator(DataUpdateCoordinator):
    """Periodically download the data from the EmmeTI Febos webapp."""

    def __init__(
        self, hass: HomeAssistant, config_entry: FebosConfigEntry, client: FebosClient
    ) -> None:
        """Initialize the data service."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
            always_update=False,
        )
        self.entities = {}
        self.client = client

    async def _async_setup(self):
        """Set up the coordinator."""
        await self.hass.async_add_executor_job(self.client.discover)

    async def _async_update_data(self) -> dict[str, Any]:
        """Async update wrapper."""
        return await self.hass.async_add_executor_job(self.client.update)
