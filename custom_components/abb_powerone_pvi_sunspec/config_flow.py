"""Config Flow for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import logging

from modbus_connection import ModbusError, ModbusTcpParams
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector

from .api import ABBPowerOneFimerAPI
from .const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_ADDR,
    DEFAULT_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_BASE_ADDR,
    MAX_DEVICE_ID,
    MAX_PORT,
    MAX_SCAN_INTERVAL,
    MIN_BASE_ADDR,
    MIN_DEVICE_ID,
    MIN_PORT,
    MIN_SCAN_INTERVAL,
)
from .helpers import host_valid, log_debug, log_error

_LOGGER = logging.getLogger(__name__)


@callback
def get_host_from_config(hass: HomeAssistant):
    """Return the hosts already configured."""
    return {
        config_entry.data.get(CONF_HOST)
        for config_entry in hass.config_entries.async_entries(DOMAIN)
    }


class ABBPowerOneFimerConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """ABB Power-One PVI SunSpec config flow."""

    VERSION = 2
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
    ) -> str | None:
        """Read the inverter and return its serial number, or None if it cannot be read."""
        log_debug(
            _LOGGER, "get_unique_id", "Test connection", host=host, port=port, device_id=device_id
        )
        params = ModbusTcpParams(host=host, port=port)
        try:
            async with async_get_temporary_unit(self.hass, params, device_id) as unit:
                api = ABBPowerOneFimerAPI(name, host, unit, base_addr)
                data = await api.async_get_data()
        except (ModbusError, HomeAssistantError) as err:
            log_error(
                _LOGGER,
                "get_unique_id",
                "Failed to connect",
                host=host,
                port=port,
                device_id=device_id,
                error=err,
            )
            return None
        return data["comm_sernum"] or None

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            name = str(user_input[CONF_NAME])
            host = str(user_input[CONF_HOST])
            port = int(user_input[CONF_PORT])
            device_id = int(user_input[CONF_DEVICE_ID])
            base_addr = int(user_input[CONF_BASE_ADDR])

            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "Device Already Configured"
            elif not host_valid(host):
                errors[CONF_HOST] = "invalid Host IP"
            else:
                uid = await self.get_unique_id(name, host, port, device_id, base_addr)
                if uid is not None:
                    log_debug(_LOGGER, "async_step_user", "Device unique id", uid=uid)
                    # Assign a unique ID to the flow and abort the flow
                    # if another flow with the same unique ID is in progress
                    await self.async_set_unique_id(uid)

                    # Abort the flow if a config entry with the same unique ID exists
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

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
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_BASE_ADDR, max=MAX_BASE_ADDR)),
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

    VERSION = 2

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
                    default=config_entry.data.get(CONF_DEVICE_ID)
                    or config_entry.data.get("slave_id"),
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
                ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_BASE_ADDR, max=MAX_BASE_ADDR)),
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
