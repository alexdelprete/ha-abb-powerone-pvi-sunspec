"""Data Update Coordinator for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ABBPowerOnePVISunSpecAPI
from .const import (
    CONF_BASE_ADDR,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class HubDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize data update coordinator."""
        # get scan_interval from user config
        self.scan_interval = config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        # enforce scan_interval lower bound
        if self.scan_interval < MIN_SCAN_INTERVAL:
            self.scan_interval = MIN_SCAN_INTERVAL
        # set coordinator update interval
        self.update_interval = timedelta(seconds=self.scan_interval)
        _LOGGER.debug(
            f"Scan Interval: scan_interval={self.scan_interval} update_interval={self.update_interval}"
        )
        # set update method and interval for coordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_method=self.async_update_data,
            update_interval=self.update_interval,
        )

        self.hub_version = 0
        self.last_update_time = datetime.now()
        self.last_update_status = ""

        self.hass = hass
        self.config_entry = config_entry
        self.name = config_entry.data.get(CONF_NAME)
        self.host = config_entry.data.get(CONF_HOST)
        self.port = config_entry.data.get(CONF_PORT)
        self.slave_id = config_entry.data.get(CONF_SLAVE_ID)
        self.base_addr = config_entry.data.get(CONF_BASE_ADDR)
        self.api = ABBPowerOnePVISunSpecAPI(
            hass,
            self.name,
            self.host,
            self.port,
            self.slave_id,
            self.base_addr,
            self.scan_interval,
        )

        _LOGGER.debug("Data: %s", config_entry.data)
        _LOGGER.debug("Options: %s", config_entry.options)
        _LOGGER.debug(
            "Setup config_entry with scan interval %s. Host: %s Port: %s ID: %s",
            self.scan_interval,
            config_entry.data.get(CONF_HOST),
            config_entry.data.get(CONF_PORT),
            config_entry.data.get(CONF_SLAVE_ID),
        )

    async def async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("ABB SunSpec Update data coordinator update")
        try:
            await self.api.async_get_data()
            self.last_update_time = datetime.now()
            self.last_update_status = "Success"

            _LOGGER.debug(f"Coordinator update completed at {self.last_update_time}")

            return True
        except Exception as ex:
            self.last_update_status = "Failed"
            _LOGGER.debug(
                f"Coordinator Update Data error: {ex} at {self.last_update_time}"
            )
            raise UpdateFailed() from ex
