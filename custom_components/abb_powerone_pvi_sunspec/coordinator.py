"""Data Update Coordinator for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

from datetime import timedelta
import logging
from typing import Any

from modbus_connection import ModbusError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ABBPowerOneFimerAPI
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .helpers import log_debug

_LOGGER = logging.getLogger(__name__)


class ABBPowerOneFimerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, api: ABBPowerOneFimerAPI
    ) -> None:
        """Initialize data update coordinator."""
        scan_interval = int(config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        scan_interval = min(max(scan_interval, MIN_SCAN_INTERVAL), MAX_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        log_debug(
            _LOGGER,
            "__init__",
            "Coordinator initialized",
            host=api.host,
            scan_interval=scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Read the inverter."""
        try:
            return await self.api.async_get_data()
        except ModbusError as err:
            raise UpdateFailed(f"Error reading inverter {self.api.name}: {err}") from err
