"""Implements HA Config Flow"""

import ipaddress
import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PORT,
                                 CONF_SCAN_INTERVAL)
from homeassistant.core import HomeAssistant, callback

from .const import (CONF_BASE_ADDR, CONF_SLAVE_ID, DEFAULT_BASE_ADDR,
                    DEFAULT_NAME, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL,
                    DEFAULT_SLAVE_ID, DOMAIN)


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
    return set(
        entry.data[CONF_HOST] for entry in hass.config_entries.async_entries(DOMAIN)
    )


class ABBPowerOnePVISunSpecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ABB Power-One PVI SunSpec Config Flow"""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "already_configured"
            elif not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "invalid host IP"
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
                    vol.Required(CONF_BASE_ADDR, default=DEFAULT_BASE_ADDR): int,
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                }
            ),
            errors=errors,
        )

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in abb_powerone_pvi_sunspec_entries(self.hass):
            return True
        return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ABBPowerOnePVISunSpecOptionsFlow(config_entry)


class ABBPowerOnePVISunSpecOptionsFlow(config_entries.OptionsFlow):
    """ABB Power-One PVI SunSpec Options Flow"""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self.settings = {}
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        port = self.config_entry.options.get(
            CONF_PORT, self.config_entry.data.get(CONF_PORT)
        )
        slave_id = self.config_entry.options.get(
            CONF_SLAVE_ID, self.config_entry.data.get(CONF_SLAVE_ID)
        )
        base_addr = self.config_entry.options.get(
            CONF_BASE_ADDR, self.config_entry.data.get(CONF_BASE_ADDR)
        )
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, self.config_entry.data.get(CONF_SCAN_INTERVAL)
        )

        if user_input is not None:
            self.settings.update(user_input)
            self.options.update(user_input)
            title = f"{self.settings[CONF_PORT]}:{self.settings[CONF_SLAVE_ID]}:{self.settings[CONF_BASE_ADDR]}:{self.settings[CONF_SCAN_INTERVAL]}"
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.settings, title=title
            )
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="user_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT, default=port): int,
                    vol.Required(CONF_SLAVE_ID, default=slave_id): int,
                    vol.Required(CONF_BASE_ADDR, default=base_addr): int,
                    vol.Required(CONF_SCAN_INTERVAL, default=scan_interval): int,
                }
            ),
            errors=errors,
        )
