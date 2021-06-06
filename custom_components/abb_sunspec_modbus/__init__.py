"""The ABB SunSpec Modbus Integration."""
import asyncio
import logging
import threading
from datetime import timedelta
from typing import Optional

import voluptuous as vol
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_STATUS,
    CONF_UNIT_ID,
)

_LOGGER = logging.getLogger(__name__)

ABB_SUNSPEC_MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.string,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: ABB_SUNSPEC_MODBUS_SCHEMA})}, extra=vol.ALLOW_EXTRA
)

PLATFORMS = ["sensor"]


async def async_setup(hass, config):
    """Set up ABB Sunspec Modbus component"""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ABB Sunspec Modbus"""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    port = entry.data[CONF_PORT]
    unit_id = entry.data[CONF_UNIT_ID]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = ABBSunSpecModbusHub(
        hass, name, host, port, unit_id, scan_interval
    )
    """Register the hub."""
    hass.data[DOMAIN][name] = {"hub": hub}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass, entry):
    """Unload ABB SunSpec Modbus entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.data["name"])
    return True


class ABBSunSpecModbusHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass,
        name,
        host,
        port,
        unit_id,
        scan_interval,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._client = ModbusTcpClient(host=host, port=port, unit_id=unit_id)
        self._lock = threading.Lock()
        self._name = name
        self._scan_interval = timedelta(seconds=scan_interval)
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

    @callback
    def async_add_abb_sunspec_sensor(self, update_callback):
        """Listen for data updates."""
        # This is the first sensor, set up interval.
        if not self._sensors:
            self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_modbus_data, self._scan_interval
            )

        self._sensors.append(update_callback)

    @callback
    def async_remove_abb_sunspec_sensor(self, update_callback):
        """Remove data update."""
        self._sensors.remove(update_callback)

        if not self._sensors:
            """stop the interval timer upon removal of last sensor"""
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        if not self._sensors:
            return

        update_result = self.read_modbus_data()

        if update_result:
            for update_callback in self._sensors:
                update_callback()

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        with self._lock:
            self._client.connect()

    def read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_holding_registers(address, count, **kwargs)

    def read_modbus_data_stub(self):
        return (
            self.read_modbus_data_inverter_stub()
        )

    def read_modbus_data(self):
        return (
            self.read_modbus_data_inverter()
        )

    def read_modbus_data_inverter_stub(self):
        self.data["accurrent"] = 1
        self.data["accurrenta"] = 1
        self.data["accurrentb"] = 1
        self.data["accurrentc"] = 1
        self.data["acvoltageab"] = 1
        self.data["acvoltagebc"] = 1
        self.data["acvoltageca"] = 1
        self.data["acvoltagean"] = 1
        self.data["acvoltagebn"] = 1
        self.data["acvoltagecn"] = 1
        self.data["acpower"] = 1
        self.data["acfreq"] = 1
        self.data["acenergy"] = 1
        self.data["dcpower"] = 1
        self.data["tempcab"] = 1
        self.data["tempoth"] = 1
        self.data["status"] = 1
        self.data["statusvendor"] = 1

        return True


    def read_modbus_data_inverter(self):
        inverter_data = self.read_holding_registers(address=72, count=100)
        if not inverter_data.isError():
            decoder = BinaryPayloadDecoder.fromRegisters(
                inverter_data.registers, byteorder=Endian.Big
            )

            # registers 72 to 75
            accurrent = decoder.decode_16bit_uint()
            accurrenta = decoder.decode_16bit_uint()
            accurrentb = decoder.decode_16bit_uint()
            accurrentc = decoder.decode_16bit_uint()

            # skip register 76
            decoder.skip_bytes(2)

            # registers 77 to 82
            acvoltageab = decoder.decode_16bit_uint()
            acvoltagebc = decoder.decode_16bit_uint()
            acvoltageca = decoder.decode_16bit_uint()
            acvoltagean = decoder.decode_16bit_uint()
            acvoltagebn = decoder.decode_16bit_uint()
            acvoltagecn = decoder.decode_16bit_uint()

            # skip register 83
            decoder.skip_bytes(2)

            # register 84
            acpower = decoder.decode_16bit_int()

            # skip register 85
            decoder.skip_bytes(2)

            # register 86
            acfreq = decoder.decode_16bit_uint()

            # skip register 87-93
            decoder.skip_bytes(14)

             # register 94
            acenergy = decoder.decode_32bit_uint()
            self.data["acenergy"] = round(acenergy * 0.001, 3)

            # skip register 96 to 100
            decoder.skip_bytes(10)

             # register 101
            dcpower = decoder.decode_16bit_int()

            # skip register 102
            decoder.skip_bytes(2)

             # register 103
            tempcab = decoder.decode_16bit_int()

            # skip registers 104-105
            decoder.skip_bytes(4)

            # register 106
            tempoth = decoder.decode_16bit_int()

            # skip register 107
            decoder.skip_bytes(2)

            # register 108
            status = decoder.decode_16bit_int()
            self.data["status"] = status

            # register 109
            statusvendor = decoder.decode_16bit_int()
            self.data["statusvendor"] = statusvendor

            # skip register 110 to 140
            decoder.skip_bytes(62)

            # registers 141 to 143
            mppt1curr = decoder.decode_16bit_uint()
            mppt1volt = decoder.decode_16bit_uint()
            mppt1power = decoder.decode_16bit_uint()

            # skip register 144 to 160
            decoder.skip_bytes(34)

            # registers 161 to 163
            mppt2curr = decoder.decode_16bit_uint()
            mppt2volt = decoder.decode_16bit_uint()
            mppt2power = decoder.decode_16bit_uint()

            return True
        else:
            return False
