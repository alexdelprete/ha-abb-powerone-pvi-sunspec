"""Config Flow for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import ipaddress
import logging
import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector
from pymodbus.exceptions import ConnectionException

from .api import ABBPowerOneFimerAPI
from .const import (
    CONF_BASE_ADDR,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_DEVICE_ID,
    DEFAULT_BASE_ADDR,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_DEVICE_ID,
    DOMAIN,
    MAX_BASE_ADDR,
    MAX_PORT,
    MAX_SCAN_INTERVAL,
    MAX_DEVICE_ID,
    MIN_BASE_ADDR,
    MIN_PORT,
    MIN_SCAN_INTERVAL,
    MIN_DEVICE_ID,
)

_LOGGER = logging.getLogger(__name__)


def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))


@callback
def get_host_from_config(hass: HomeAssistant):
    """Return the hosts already configured."""
    return {
        config_entry.data.get(CONF_HOST)
        for config_entry in hass.config_entries.async_entries(DOMAIN)
    }


class ABBPowerOneFimerConfigFlow(ConfigFlow, domain=DOMAIN):
    """ABB Power-One PVI SunSpec config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Initiate Options Flow Instance."""
        return ABBPowerOneFimerOptionsFlow(config_entry)

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in get_host_from_config(self.hass):
            return True
        return False

    async def get_unique_id(
        self,
        name: str,
        host: str,
        port: int,
        device_id: int,
        base_addr: int,
        scan_interval: int,
    ):
        """Return device serial number."""
        self._name = str(name)
        self._host = str(host)
        self._port = int(port)
        self._device_id = int(device_id)
        self._base_addr = int(base_addr)
        self._scan_interval = int(scan_interval)

        _LOGGER.debug(
            f"Test connection to {self._host}:{self._port} device id {self._device_id}"
        )
        try:
            _LOGGER.debug("Creating API Client")
            self.api = ABBPowerOneFimerAPI(
                self.hass,
                self._name,
                self._host,
                self._port,
                self._device_id,
                self._base_addr,
                self._scan_interval,
            )
            _LOGGER.debug("API Client created: calling get data")
            self.api_data = await self.api.async_get_data()
            _LOGGER.debug("API Client: get data")
            _LOGGER.debug(f"API Client Data: {self.api_data}")
            return self.api.data["comm_sernum"]
        except ConnectionException as connerr:
            _LOGGER.error(
                f"Failed to connect to host: {self._host}:{self._port} - device id: {self._device_id} - Exception: {connerr}"
            )
            return False

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            name = str(user_input[CONF_NAME])
            host = str(user_input[CONF_HOST])
            port = int(user_input[CONF_PORT])
            device_id = int(user_input[CONF_DEVICE_ID])
            base_addr = int(user_input[CONF_BASE_ADDR])
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])

            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "Device Already Configured"
            elif not host_valid(host):
                errors[CONF_HOST] = "invalid Host IP"
            else:
                uid = await self.get_unique_id(
                    name, host, port, device_id, base_addr, scan_interval
                )
                if uid is not False:
                    _LOGGER.debug(f"Device unique id: {uid}")
                    # Assign a unique ID to the flow and abort the flow
                    # if another flow with the same unique ID is in progress
                    await self.async_set_unique_id(uid)

                    # Abort the flow if a config entry with the same unique ID exists
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )

                errors[CONF_HOST] = "Connection to device failed (S/N not retreived)"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=DEFAULT_NAME,
                    ): cv.string,
                    vol.Required(
                        CONF_HOST,
                    ): cv.string,
                    vol.Required(
                        CONF_PORT,
                        default=DEFAULT_PORT,
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_PORT, max=MAX_PORT)),
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=DEFAULT_DEVICE_ID,
                    ): selector(
                        {
                            "number": {
                                "min": MIN_DEVICE_ID,
                                "max": MAX_DEVICE_ID,
                                "step": 1,
                                "mode": "box",
                            }
                        }
                    ),
                    vol.Required(
                        CONF_BASE_ADDR,
                        default=DEFAULT_BASE_ADDR,
                    ): vol.All(
                        vol.Coerce(int), vol.Clamp(min=MIN_BASE_ADDR, max=MAX_BASE_ADDR)
                    ),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Clamp(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                },
            ),
            errors=errors,
        )


class ABBPowerOneFimerOptionsFlow(OptionsFlow):
    """Config flow options handler."""

    VERSION = 1

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize option flow instance."""
        self.data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=config_entry.data.get(CONF_HOST),
                ): cv.string,
                vol.Required(
                    CONF_PORT,
                    default=config_entry.data.get(CONF_PORT),
                ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_PORT, max=MAX_PORT)),
                vol.Required(
                    CONF_DEVICE_ID,
                    default=config_entry.data.get(CONF_DEVICE_ID),
                ): selector(
                    {
                        "number": {
                            "min": MIN_DEVICE_ID,
                            "max": MAX_DEVICE_ID,
                            "step": 1,
                            "mode": "box",
                        }
                    }
                ),
                vol.Required(
                    CONF_BASE_ADDR,
                    default=config_entry.data.get(CONF_BASE_ADDR),
                ): vol.All(
                    vol.Coerce(int), vol.Clamp(min=MIN_BASE_ADDR, max=MAX_BASE_ADDR)
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=config_entry.data.get(CONF_SCAN_INTERVAL),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Clamp(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            # complete non-edited entries before update (ht @PeteRage)
            if CONF_NAME in self.config_entry.data:
                user_input[CONF_NAME] = self.config_entry.data.get(CONF_NAME)

            # write updated config entries (ht @PeteRage / @fuatakgun)
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            self.async_abort(reason="configuration updated")

            # write empty options entries (ht @PeteRage / @fuatakgun)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=self.data_schema)
