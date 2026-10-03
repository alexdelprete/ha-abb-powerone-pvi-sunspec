"""Config Flow for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

from collections.abc import Mapping
import logging
from typing import Any

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
from .helpers import host_valid, log_debug

_LOGGER = logging.getLogger(__name__)


DEVICE_ID_SELECTOR = selector(
    {"number": {"min": MIN_DEVICE_ID, "max": MAX_DEVICE_ID, "step": 1, "mode": "box"}}
)
PORT_VALIDATOR = vol.All(vol.Coerce(int), vol.Clamp(min=MIN_PORT, max=MAX_PORT))
BASE_ADDR_VALIDATOR = vol.All(vol.Coerce(int), vol.Clamp(min=MIN_BASE_ADDR, max=MAX_BASE_ADDR))
SCAN_INTERVAL_VALIDATOR = vol.All(
    vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): PORT_VALIDATOR,
        vol.Required(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): DEVICE_ID_SELECTOR,
        vol.Required(CONF_BASE_ADDR, default=DEFAULT_BASE_ADDR): BASE_ADDR_VALIDATOR,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_VALIDATOR,
    }
)


def connection_settings(data: Mapping[str, Any]) -> tuple[str, int, int, int]:
    """Return the settings that select the inverter: host, port, unit id and base address."""
    device_id = data.get(CONF_DEVICE_ID) or data.get("slave_id") or 0
    return (
        str(data.get(CONF_HOST)),
        int(data.get(CONF_PORT) or 0),
        int(device_id),
        int(data.get(CONF_BASE_ADDR) or 0),
    )


@callback
def get_host_from_config(hass: HomeAssistant) -> set[str]:
    """Return the hosts already configured."""
    return {
        str(config_entry.data[CONF_HOST])
        for config_entry in hass.config_entries.async_entries(DOMAIN)
        if CONF_HOST in config_entry.data
    }


async def async_read_serial_number(
    hass: HomeAssistant, data: dict[str, Any]
) -> tuple[str | None, dict[str, str]]:
    """Read the inverter that ``data`` points at.

    Returns its serial number and no errors, or None and the form errors.
    """
    host = str(data[CONF_HOST])
    if not host_valid(host):
        return None, {CONF_HOST: "invalid_host"}

    port = int(data[CONF_PORT])
    device_id = int(data[CONF_DEVICE_ID])
    params = ModbusTcpParams(host=host, port=port)
    api: ABBPowerOneFimerAPI | None = None
    try:
        async with async_get_temporary_unit(hass, params, device_id) as unit:
            api = ABBPowerOneFimerAPI(
                str(data.get(CONF_NAME, DEFAULT_NAME)), host, unit, int(data[CONF_BASE_ADDR])
            )
            await api.async_get_data()
    except HomeAssistantError as err:
        # another integration holds this device with different link settings
        log_debug(_LOGGER, "async_read_serial_number", "Link conflict", host=host, error=err)
        return None, {"base": "modbus_link_conflict"}
    except (ModbusError, OSError) as err:
        log_debug(
            _LOGGER,
            "async_read_serial_number",
            "Cannot connect",
            host=host,
            port=port,
            device_id=device_id,
            error=err,
        )
        return None, {"base": "cannot_connect"}
    except Exception:
        _LOGGER.exception("Unexpected error reading the inverter at %s", host)
        return None, {"base": "unknown"}

    if not (serial := api.data["comm_sernum"]):
        return None, {"base": "no_serial_number"}
    log_debug(_LOGGER, "async_read_serial_number", "Inverter found", host=host, serial=serial)
    return serial, {}


class ABBPowerOneFimerConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """ABB Power-One PVI SunSpec config flow."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Initiate Options Flow Instance."""
        return ABBPowerOneFimerOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_HOST] in get_host_from_config(self.hass):
                errors[CONF_HOST] = "already_configured"
            else:
                serial, errors = await async_read_serial_number(self.hass, user_input)
                if serial is not None:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )


class ABBPowerOneFimerOptionsFlow(OptionsFlow):
    """Config flow options handler."""

    VERSION = 2

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize option flow instance."""
        data = config_entry.data
        self.data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=data.get(CONF_HOST)): cv.string,
                vol.Required(CONF_PORT, default=data.get(CONF_PORT)): PORT_VALIDATOR,
                vol.Required(
                    CONF_DEVICE_ID, default=data.get(CONF_DEVICE_ID) or data.get("slave_id")
                ): DEVICE_ID_SELECTOR,
                vol.Required(CONF_BASE_ADDR, default=data.get(CONF_BASE_ADDR)): BASE_ADDR_VALIDATOR,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ): SCAN_INTERVAL_VALIDATOR,
            }
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options.

        New connection settings are tested first and must reach the same
        inverter; a polling-interval change alone is saved without a test, so it
        works while the inverter is unreachable (e.g. at night).
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            entry = self.config_entry
            # keep the name, which the options form does not edit (ht @PeteRage)
            new_data = {**user_input}
            if CONF_NAME in entry.data:
                new_data[CONF_NAME] = entry.data[CONF_NAME]

            if connection_settings(new_data) != connection_settings(entry.data):
                serial, errors = await async_read_serial_number(self.hass, new_data)
                if serial is not None and entry.unique_id and serial != entry.unique_id:
                    errors = {"base": "wrong_device"}

            if not errors:
                # write updated config entries (ht @PeteRage / @fuatakgun)
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(self.data_schema, user_input),
            errors=errors,
        )
