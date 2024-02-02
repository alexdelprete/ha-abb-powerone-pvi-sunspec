"""Config Flow for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import ipaddress
import logging
import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector
from pymodbus.exceptions import ConnectionException

from .api import ABBPowerOnePVISunSpecHub
from .const import (
    CONF_BASE_ADDR,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_BASE_ADDR,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
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
def abb_powerone_pvi_sunspec_entries(hass: HomeAssistant):
    """Return the hosts already configured."""
    return {
        config_entry.data.get(CONF_HOST)
        for config_entry in hass.config_entries.async_entries(DOMAIN)
    }


class ABBPowerOnePVISunSpecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ABB Power-One PVI SunSpec config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Initiate Options Flow Instance."""
        return ABBPowerOnePVISunSpecOptionsFlow(config_entry)

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in abb_powerone_pvi_sunspec_entries(self.hass):
            return True
        return False

    async def test_connection(
        self, name, host, port, slave_id, base_addr, scan_interval
    ):
        """Return true if credentials is valid."""
        _LOGGER.debug(f"Test connection to {host}:{port} slave id {slave_id}")
        try:
            _LOGGER.debug("Creating Hub")
            self.hub = ABBPowerOnePVISunSpecHub(
                self.hass, name, host, port, slave_id, base_addr, scan_interval
            )
            _LOGGER.debug("Hub created: calling get data")
            self.hub_data = await self.hub.async_get_data()
            _LOGGER.debug("After Hub, get data")
            _LOGGER.debug(f"Hub Data: {self.hub_data}")
            return self.hub.data["comm_sernum"]
        except ConnectionException as connerr:
            _LOGGER.error(
                f"Failed to connect to host: {host}:{port} - slave id: {slave_id} - Exception: {connerr}"
            )
            return False

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            name = user_input[CONF_NAME]
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            slave_id = user_input[CONF_SLAVE_ID]
            base_addr = user_input[CONF_BASE_ADDR]
            scan_interval = user_input[CONF_SCAN_INTERVAL]

            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "Device Already Configured"
            elif not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "invalid Host IP"
            else:
                uid = await self.test_connection(
                    name, host, port, slave_id, base_addr, scan_interval
                )
                if uid is not False:
                    _LOGGER.debug(f"Device unique id: {uid}")
                    await self.async_set_unique_id(uid)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )
                else:
                    errors[
                        CONF_HOST
                    ] = "Connection to device failed (S/N not retreived)"

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
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_SLAVE_ID,
                        default=DEFAULT_SLAVE_ID,
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_BASE_ADDR,
                        default=DEFAULT_BASE_ADDR,
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): selector(
                        {
                            "number": {
                                "min": 30,
                                "max": 600,
                                "step": 10,
                                "unit_of_measurement": "s",
                                "mode": "slider",
                            }
                        }
                    ),
                },
            ),
            errors=errors,
        )


class ABBPowerOnePVISunSpecOptionsFlow(config_entries.OptionsFlow):
    """Config flow options handler."""

    VERSION = 1

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize option flow instance."""
        self.config_entry = config_entry
        self.data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_PORT,
                    default=self.config_entry.data.get(CONF_PORT),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_SLAVE_ID,
                    default=self.config_entry.data.get(CONF_SLAVE_ID),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_BASE_ADDR,
                    default=self.config_entry.data.get(CONF_BASE_ADDR),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.data.get(CONF_SCAN_INTERVAL),
                ): selector(
                    {
                        "number": {
                            "min": 30,
                            "max": 600,
                            "step": 10,
                            "unit_of_measurement": "s",
                            "mode": "slider",
                        }
                    }
                ),
            }
        )

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            # complete non-edited entries before update (ht @PeteRage)
            if CONF_NAME in self.config_entry.data:
                user_input[CONF_NAME] = self.config_entry.data.get(CONF_NAME)
            if CONF_HOST in self.config_entry.data:
                user_input[CONF_HOST] = self.config_entry.data.get(CONF_HOST)

            # write updated config entries (ht @PeteRage / @fuatakgun)
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            self.async_abort(reason="configuration updated")

            # write empty options entries (ht @PeteRage / @fuatakgun)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=self.data_schema)
