"""EmmeTI Febos data update coordinator."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import timedelta
from typing import Any

from httpx import HTTPStatusError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER
from .session import FebosSession


class FebosDataUpdateCoordinator(DataUpdateCoordinator):
    """Periodically download the data from the EmmeTI Febos webapp."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry[FebosDataUpdateCoordinator],
        session: FebosSession,
    ) -> None:
        """Initialize the data update coordinator.

        Args:
            hass: The Home Assistant instance.
            config_entry: The config entry for this integration.
            session: An authenticated FebosSession object.
        """
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )
        self.session = session
        self._write_lock = asyncio.Lock()

    def do_update(self):
        """Update data from the Febos API.

        Handles HTTP 401 errors by re-authenticating and retrying.

        Returns:
            Updated data dictionary from the Febos session.

        Raises:
            UpdateFailed: If the update fails for any reason.
        """
        try:
            return self.session.update()
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                LOGGER.debug(f"Attempting reauthentication due to: '{e}'")
                self.session.login()
                return self.session.update()
            LOGGER.error(f"Failed to update data: {e}")
            raise UpdateFailed(f"Failed to update data: {e}") from e
        except Exception as e:
            LOGGER.error(f"Unexpected error during data update: {e}")
            raise UpdateFailed(f"Unexpected error during data update: {e}") from e

    async def _async_setup(self) -> None:
        """Set up the coordinator by discovering Febos devices and resources."""
        await self.hass.async_add_executor_job(self.session.discover)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the Febos API.

        Returns:
            Dictionary of updated sensor and binary sensor values.
        """
        return await self.hass.async_add_executor_job(self.do_update)

    async def async_set_value(self, key: str, value: Any) -> None:
        async with self._write_lock:
            data = await self.hass.async_add_executor_job(
                lambda: self.session.set_value(key=key, value=value)
            )
            if data:
                self.async_set_updated_data(data)
