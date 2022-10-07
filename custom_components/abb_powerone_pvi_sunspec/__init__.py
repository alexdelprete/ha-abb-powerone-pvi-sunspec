"""The ABB Power-One PVI SunSpec Integration"""
import asyncio
import logging
import threading
from datetime import timedelta
from typing import Optional

import voluptuous as vol
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.exceptions import ConnectionException

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_SLAVE_ID,
    CONF_BASE_ADDR,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_BASE_ADDR,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_STATUS,
    DEVICE_GLOBAL_STATUS,
    DEVICE_MODEL,
    INVERTER_TYPE
)

_LOGGER = logging.getLogger(__name__)

ABB_POWERONE_PVI_SUNSPEC_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
        vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): cv.positive_int,
        vol.Required(CONF_BASE_ADDR, default=DEFAULT_BASE_ADDR): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: ABB_POWERONE_PVI_SUNSPEC_SCHEMA})}, extra=vol.ALLOW_EXTRA
)

PLATFORMS = ["sensor"]


async def async_setup(hass, config):
    """Set up ABB Power-One PVI SunSpec component"""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ABB Power-One PVI SunSpec"""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    port = entry.data[CONF_PORT]
    slave_id = entry.data[CONF_SLAVE_ID]
    base_addr = entry.data[CONF_BASE_ADDR]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = ABBPowerOnePVISunSpecHub(
        hass, name, host, port, slave_id, base_addr, scan_interval
    )
    """Register the hub."""
    hass.data[DOMAIN][name] = {"hub": hub}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass, entry):
    """Unload ABB Power-One PVI SunSpec entry."""
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


class ABBPowerOnePVISunSpecHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass,
        name,
        host,
        port,
        slave_id,
        base_addr,
        scan_interval,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._client = ModbusTcpClient(host=host, port=port)
        self._lock = threading.Lock()
        self._name = name
        self._slave_id = slave_id
        self._base_addr = base_addr
        self._scan_interval = timedelta(seconds=scan_interval)
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

    @callback
    def async_add_sunspec_modbus_sensor(self, update_callback):
        """Listen for data updates."""
        # This is the first sensor, set up interval.
        if not self._sensors:
            self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_sunspec_modbus_data, self._scan_interval
            )

        self._sensors.append(update_callback)

    @callback
    def async_remove_sunspec_modbus_sensor(self, update_callback):
        """Remove data update."""
        self._sensors.remove(update_callback)

        if not self._sensors:
            """stop the interval timer upon removal of last sensor"""
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_sunspec_modbus_data(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        if not self._sensors:
            return

        update_result = self.read_sunspec_modbus_data()

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

    def calculate_value(self, value, sf):
        return value * 10 ** sf

    def read_sunspec_modbus_data_stub(self):
        return (
            self.read_sunspec_modbus_stub()
        )

    def read_sunspec_modbus_data(self):
        try:
            return self.read_sunspec_modbus_model_1() and self.read_sunspec_modbus_model_101_103() and self.read_sunspec_modbus_model_160()
        except ConnectionException as ex:
            _LOGGER.error("(read_data) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.error("(read_data) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

    def read_sunspec_modbus_stub(self):
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
        self.data["comm_options"] = 1
        self.data["comm_manufact"] = ""
        self.data["comm_model"] = ""
        self.data["comm_version"] = ""
        self.data["comm_sernum"] = ""
        self.data["dccurr"] = 1
        self.data["dcvolt"] = 1
        self.data["dcpower"] = 1
        self.data["dc1curr"] = 1
        self.data["dc1volt"] = 1
        self.data["dc1power"] = 1
        self.data["dc2curr"] = 1
        self.data["dc2volt"] = 1
        self.data["dc2power"] = 1
        self.data["invtype"] = ""
        self.data["status"] = ""
        self.data["statusvendor"] = ""
        self.data["totalenergy"] = 1
        self.data["tempcab"] = 1
        self.data["tempoth"] = 1
        return True


    def read_sunspec_modbus_model_1(self):
        # A single register is 2 bytes. Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 72 read 92 registers to read (M101 or M103)+M160 (Realtime Power/Energy Data) in 1-pass
        read_model_1_data = self.read_holding_registers(unit=self._slave_id, address=(self._base_addr + 4), count=64)
        _LOGGER.debug("(read_inv) Slave ID: %s", self._slave_id)
        _LOGGER.debug("(read_inv) Base Address: %s", self._base_addr)
        if read_model_1_data.isError():
            _LOGGER.error("(read_inv) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.error("(read_inv) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_1_data.registers, byteorder=Endian.Big
        )

        # registers 4 to 43
        comm_manufact = decoder.decode_string(size=32).decode("ascii")
        comm_model = decoder.decode_string(size=32).decode("ascii")
        comm_options = decoder.decode_string(size=16).decode("ascii")
        _LOGGER.debug("(read_inv) Manufacturer: %s", comm_manufact)
        _LOGGER.debug("(read_inv) Model: %s", comm_model)
        _LOGGER.debug("(read_inv) Options: %s", comm_options)
        self.data["comm_manufact"] = str(comm_manufact)
        self.data["comm_options"] = str(comm_options)

        # Model based on options register, if unknown, raise an error to report it
        # First char is the model: if non-printable char, hex string of the char is provided
        # So we need to check if it's a char or an hex value string and convert both to a number
        # Then we lookup in the model table, if it's there, good, otherwise we provide the given model
        opt_model = self.data["comm_options"]
        if opt_model.startswith('0x'):
            opt_model = int(opt_model[0:3], 16)
        else:
            opt_model = ord(opt_model[0])

        if opt_model in DEVICE_MODEL:
            self.data["comm_model"] = DEVICE_MODEL[opt_model]
        else:
            _LOGGER.error("(read_inv) Model unknown, report to @alexdelprete on the forum the following data: Manuf.: %s - Model: %s - Options: %s - OptModel: %s", self.data["comm_manufact"], self.data["comm_model"], self.data["comm_options"], opt_model)
            self.data["comm_model"] = str(comm_model)

        # registers 44 to 67
        comm_version = decoder.decode_string(size=16).decode("ascii")
        comm_sernum = decoder.decode_string(size=32).decode("ascii")
        _LOGGER.debug("(read_inv) Version: %s", comm_version)
        _LOGGER.debug("(read_inv) Sernum: %s", comm_sernum)
        self.data["comm_version"] = str(comm_version)
        self.data["comm_sernum"] = str(comm_sernum)

        return True

    def read_sunspec_modbus_model_101_103(self):
        # Max number of registers in one read for Modbus/TCP is 123
        # (ref.: https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251)
        #
        # So we could do 2 sweeps, one for M1 and the other for M103+M160. Since some old inverters have problems
        # with large sweeps, we'll split it in 3 sweeps:
        #   - Sweep 1 (M1): Start address 4 read 64 registers to read M1 (Common Inverter Info)
        #   - Sweep 2 (M103): Start address 70 read 40 registers to read M103+M160 (Realtime Power/Energy Data)
        #   - Sweep 3 (M160): Start address 124 read 40 registers to read M1 (Common Inverter Info)
        read_model_101_103_data = self.read_holding_registers(unit=self._slave_id, address=(self._base_addr + 70), count=40)
        _LOGGER.debug("(read_rt_1) Slave ID: %s", self._slave_id)
        _LOGGER.debug("(read_rt_1) Base Address: %s", self._base_addr)
        if read_model_101_103_data.isError():
            _LOGGER.error("(read_rt_1) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.error("(read_rt_1) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_101_103_data.registers, byteorder=Endian.Big
        )

        # register 70
        invtype = decoder.decode_16bit_uint()
        _LOGGER.debug("(read_rt_1) Inverter Type (int): %s", invtype)
        _LOGGER.debug("(read_rt_1) Inverter Type (str): %s", INVERTER_TYPE[invtype])
        # make sure the value is in the known status list
        if invtype not in INVERTER_TYPE:
            invtype = 999
            _LOGGER.error("(read_rt_1) Inverter Type Unknown (int): %s", invtype)
            _LOGGER.error("(read_rt_1) Inverter Type Unknown (str): %s", INVERTER_TYPE[invtype])
        self.data["invtype"] = INVERTER_TYPE[invtype]

        # skip register 71
        decoder.skip_bytes(2)

        # registers 72 to 76
        accurrent = decoder.decode_16bit_uint()

        if self.data["invtype"] == "Three Phase":
            accurrenta = decoder.decode_16bit_uint()
            accurrentb = decoder.decode_16bit_uint()
            accurrentc = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(6)

        accurrentsf = decoder.decode_16bit_int()
        accurrent = self.calculate_value(accurrent, accurrentsf)
        self.data["accurrent"] = round(accurrent, abs(accurrentsf))

        if self.data["invtype"] == "Three Phase":
            accurrenta = self.calculate_value(accurrenta, accurrentsf)
            accurrentb = self.calculate_value(accurrentb, accurrentsf)
            accurrentc = self.calculate_value(accurrentc, accurrentsf)
            self.data["accurrenta"] = round(accurrenta, abs(accurrentsf))
            self.data["accurrentb"] = round(accurrentb, abs(accurrentsf))
            self.data["accurrentc"] = round(accurrentc, abs(accurrentsf))

        # registers 77 to 83
        if self.data["invtype"] == "Three Phase":
            acvoltageab = decoder.decode_16bit_uint()
            acvoltagebc = decoder.decode_16bit_uint()
            acvoltageca = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(6)

        acvoltagean = decoder.decode_16bit_uint()

        if self.data["invtype"] == "Three Phase":
            acvoltagebn = decoder.decode_16bit_uint()
            acvoltagecn = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(4)

        acvoltagesf = decoder.decode_16bit_int()

        acvoltagean = self.calculate_value(acvoltagean, acvoltagesf)
        self.data["acvoltagean"] = round(acvoltagean, abs(acvoltagesf))

        if self.data["invtype"] == "Three Phase":
            acvoltageab = self.calculate_value(acvoltageab, acvoltagesf)
            acvoltagebc = self.calculate_value(acvoltagebc, acvoltagesf)
            acvoltageca = self.calculate_value(acvoltageca, acvoltagesf)
            acvoltagebn = self.calculate_value(acvoltagebn, acvoltagesf)
            acvoltagecn = self.calculate_value(acvoltagecn, acvoltagesf)
            self.data["acvoltageab"] = round(acvoltageab, abs(acvoltagesf))
            self.data["acvoltagebc"] = round(acvoltagebc, abs(acvoltagesf))
            self.data["acvoltageca"] = round(acvoltageca, abs(acvoltagesf))
            self.data["acvoltagebn"] = round(acvoltagebn, abs(acvoltagesf))
            self.data["acvoltagecn"] = round(acvoltagecn, abs(acvoltagesf))

        # registers 84 to 85
        acpower = decoder.decode_16bit_int()
        acpowersf = decoder.decode_16bit_int()
        acpower = self.calculate_value(acpower, acpowersf)
        self.data["acpower"] = round(acpower, abs(acpowersf))

        # registers 86 to 87
        acfreq = decoder.decode_16bit_uint()
        acfreqsf = decoder.decode_16bit_int()
        acfreq = self.calculate_value(acfreq, acfreqsf)
        self.data["acfreq"] = round(acfreq, abs(acfreqsf))

        # skip register 88-93
        decoder.skip_bytes(12)

        # registers 94 to 96
        totalenergy = decoder.decode_32bit_uint()
        totalenergysf = decoder.decode_16bit_uint()
        totalenergy = self.calculate_value(totalenergy, totalenergysf)
        self.data["totalenergy"] = totalenergy

        # registers 97 to 100 (for monophase inverters)
        if invtype == 101:
            dccurr = decoder.decode_16bit_int()
            dccurrsf = decoder.decode_16bit_int()
            dcvolt = decoder.decode_16bit_int()
            dcvoltsf = decoder.decode_16bit_int()
            dccurr = self.calculate_value(dccurr, dccurrsf)
            dcvolt = self.calculate_value(dcvolt, dcvoltsf)
            self.data["dccurr"] = round(dccurr, abs(dccurrsf))
            self.data["dcvolt"] = round(dcvolt, abs(dcvoltsf))
        else:
            decoder.skip_bytes(8)

        # registers 101 to 102
        dcpower = decoder.decode_16bit_int()
        dcpowersf = decoder.decode_16bit_int()
        dcpower = self.calculate_value(dcpower, dcpowersf)
        self.data["dcpower"] = round(dcpower, abs(dcpowersf))

        # register 103
        tempcab = decoder.decode_16bit_int()
        # skip registers 104-105
        decoder.skip_bytes(4)
        # register 106 to 107
        tempoth = decoder.decode_16bit_int()
        tempsf = decoder.decode_16bit_int()
        # Fix for tempcab: in some inverters SF must be -2 not -1 as per specs
        tempcab_fix = tempcab
        tempcab = self.calculate_value(tempcab, tempsf)
        if tempcab > 50:
            tempcab = self.calculate_value(tempcab_fix, -2)
        tempoth = self.calculate_value(tempoth, tempsf)
        self.data["tempoth"] = round(tempoth, abs(tempsf))
        self.data["tempcab"] = round(tempcab, abs(tempsf))

        # register 108
        status = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if status not in DEVICE_STATUS:
            _LOGGER.error("Unknown Operating State: %s", status)
            status = 999
        self.data["status"] = DEVICE_STATUS[status]

        # register 109
        statusvendor = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if statusvendor not in DEVICE_GLOBAL_STATUS:
            _LOGGER.error("(init) Unknown Vendor Operating State: %s", statusvendor)
            statusvendor = 999
        self.data["statusvendor"] = DEVICE_GLOBAL_STATUS[statusvendor]

        return True


    def read_sunspec_modbus_model_160(self):
        # Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 70 read 94 registers to read M103+M160 (Realtime Power/Energy Data) in 1-pass
        read_model_160_data = self.read_holding_registers(unit=self._slave_id, address=(self._base_addr + 124), count=40)
        _LOGGER.debug("(read_rt_2) Slave ID: %s", self._slave_id)
        _LOGGER.debug("(read_rt_2) Base Address: %s", self._base_addr)
        if read_model_160_data.isError():
            _LOGGER.error("(read_rt_2) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.error("(read_rt_2) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_160_data.registers, byteorder=Endian.Big
        )

        if self.data["invtype"] == "Three Phase":
            # registers 124 to 126
            dcasf = decoder.decode_16bit_int()
            dcvsf = decoder.decode_16bit_int()
            dcwsf = decoder.decode_16bit_int()

            # skip register 127 to 140
            decoder.skip_bytes(28)

            # registers 141 to 143
            dc1curr = decoder.decode_16bit_uint()
            dc1volt = decoder.decode_16bit_uint()
            dc1power = decoder.decode_16bit_uint()
            dc1curr = self.calculate_value(dc1curr, dcasf)
            self.data["dc1curr"] = round(dc1curr, abs(dcasf))
            dc1volt = self.calculate_value(dc1volt, dcvsf)
            self.data["dc1volt"] = round(dc1volt, abs(dcvsf))
            dc1power = self.calculate_value(dc1power, dcwsf)
            self.data["dc1power"] = round(dc1power, abs(dcwsf))

            # skip register 144 to 160
            decoder.skip_bytes(34)

            # registers 161 to 163
            dc2curr = decoder.decode_16bit_uint()
            dc2volt = decoder.decode_16bit_uint()
            dc2power = decoder.decode_16bit_uint()
            dc2curr = self.calculate_value(dc2curr, dcasf)
            self.data["dc2curr"] = round(dc2curr, abs(dcasf))
            dc2volt = self.calculate_value(dc2volt, dcvsf)
            self.data["dc2volt"] = round(dc2volt, abs(dcvsf))
            dc2power = self.calculate_value(dc2power, dcwsf)
            self.data["dc2power"] = round(dc2power, abs(dcwsf))

        return True
