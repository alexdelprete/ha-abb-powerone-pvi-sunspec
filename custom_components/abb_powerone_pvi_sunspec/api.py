"""Hub Implementation"""

import logging
from datetime import timedelta
from typing import Optional

from homeassistant.core import callback
from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.pdu import ExceptionResponse

from .const import (DEVICE_GLOBAL_STATUS, DEVICE_MODEL, DEVICE_STATUS,
                    INVERTER_TYPE)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ABBPowerOnePVISunSpecHub:
    """Thread safe wrapper class for pymodbus"""

    def __init__(
        self,
        hass,
        name,
        host,
        port,
        slave_id,
        base_addr,
    ):
        """Initialize the Modbus hub"""
        self._hass = hass
        self._name = name
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._base_addr = base_addr
        self._client = ModbusTcpClient(host=self._host, port=self._port)
        self._sensors = []
        self.data = {}
        # Initialize ModBus data structure before first read
        self.init_modbus_data()


    @property
    def name(self):
        """Return the name of this hub"""
        return self._name


    def close(self):
        """Disconnect client"""
        try:
            self._client.close()
            return True
        except ConnectionException as connerr:
            _LOGGER.debug("Connection ERROR: exception in pymodbus {connerr}")
            return False


    def connect(self):
        """Connect client"""
        try:
            self._client.connect()
            return True
        except ConnectionException as connerr:
            _LOGGER.debug("Connection ERROR: exception in pymodbus {connerr}")
            return False


    def read_holding_registers(self, slave, address, count):
        """Read holding registers"""
        kwargs = {"slave": slave} if slave else {}
        try:
            res = self._client.read_holding_registers(address, count, **kwargs)
            return res
        except Exception as exc:
            _LOGGER.error(f"Failed to connect to host: {self._host}:{self._port} - slave id: {self._slave_id} - Exception: {exc}")
            return False        # except ConnectionException as connerr:
        # except ConnectionException as connerr:
        #     _LOGGER.debug("Connection ERROR: exception in pymodbus {connerr}")
        #     return False
        # except ModbusException as modbuserr:
        #     _LOGGER.debug("Modbus ERROR: exception in pymodbus {modbuserr}")
        #     return False
        # except ExceptionResponse as pduerr:
        #     _LOGGER.debug("PDU ERROR: exception in pymodbus {pduerr}")
        #     return False


    def calculate_value(self, value, scalefactor):
        """Apply Scale Factor"""
        return value * 10 ** scalefactor


    def init_modbus_data(self):
        """Initialize Dataset"""
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


    async def async_get_data(self):
        """Main Read Function"""
        try:
            _LOGGER.debug("Start Get data (Slave ID: %s - Base Address: %s)", self._slave_id, self._base_addr)
            self.connect()
            self.read_sunspec_modbus_model_1()
            self.read_sunspec_modbus_model_101_103()
            self.read_sunspec_modbus_model_160()
            self.close()
            _LOGGER.debug("End Get data")
            return True
        except Exception as exc:
            _LOGGER.error(f"Failed to connect to host: {self._host}:{self._port} - slave id: {self._slave_id} - Exception: {exc}")
            return False        # except ConnectionException as connerr:
        #     _LOGGER.debug("Connection ERROR: exception in pymodbus {connerr}")
        #     return False
        # except ModbusException as modbuserr:
        #     _LOGGER.debug("Modbus ERROR: exception in pymodbus {modbuserr}")
        #     return False
        # except ExceptionResponse as pduerr:
        #     _LOGGER.debug("PDU ERROR: exception in pymodbus {pduerr}")
        #     return False


    def read_sunspec_modbus_model_1(self):
        """Read SunSpec Model 1 Data"""
        # A single register is 2 bytes. Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 72 read 92 registers to read (M101 or M103)+M160 (Realtime Power/Energy Data) in 1-pass
        try:
            read_model_1_data = self.read_holding_registers(slave=self._slave_id, address=(self._base_addr + 4), count=64)
            _LOGGER.debug("(read_rt_1) Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_1) Base Address: %s", self._base_addr)
        except ModbusException:
            _LOGGER.debug("(read_rt_1) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_1) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_1_data.registers, byteorder=Endian.BIG
        )

        # registers 4 to 43
        comm_manufact = str.strip(decoder.decode_string(size=32).decode("ascii"))
        comm_model = str.strip(decoder.decode_string(size=32).decode("ascii"))
        comm_options = str.strip(decoder.decode_string(size=16).decode("ascii"))
        _LOGGER.debug("(read_rt_1) Manufacturer: %s", comm_manufact)
        _LOGGER.debug("(read_rt_1) Model: %s", comm_model)
        _LOGGER.debug("(read_rt_1) Options: %s", comm_options)
        self.data["comm_manufact"] = comm_manufact.rstrip(' \t\r\n\0\u0000')
        self.data["comm_model"] = comm_model.rstrip(' \t\r\n\0\u0000')
        self.data["comm_options"] = comm_options.rstrip(' \t\r\n\0\u0000')
        # Model based on options register, if unknown, raise an error to report it
        # First char is the model: if non-printable char, hex string of the char is provided
        # So we need to check if it's a char or an hex value string and convert both to a number
        # Then we lookup in the model table, if it's there, good, otherwise we provide the given model
        # test also with opt_model = '0x0DED/0xFFFF'
        opt_model = self.data["comm_options"]
        if opt_model.startswith('0x'):
            opt_model_int = int(opt_model[0:4], 16)
            _LOGGER.debug("(opt_notprintable) opt_model: %s - opt_model_int: %s", opt_model, opt_model_int)
        else:
            opt_model_int = ord(opt_model[0])
            _LOGGER.debug("(opt_printable) opt_model: %s - opt_model_int: %s", opt_model, opt_model_int)
        if opt_model_int in DEVICE_MODEL:
            self.data["comm_model"] = DEVICE_MODEL[opt_model_int]
            _LOGGER.debug("(opt_comm_model) comm_model: %s", self.data["comm_model"])
        else:
            _LOGGER.error("(opt_comm_model) Model unknown, report to @alexdelprete on the forum the following data: Manuf.: %s - Model: %s - Options: %s - OptModel: %s - OptModelInt: %s", self.data["comm_manufact"], self.data["comm_model"], self.data["comm_options"], opt_model, opt_model_int)

        # registers 44 to 67
        comm_version = str.strip(decoder.decode_string(size=16).decode("ascii"))
        comm_sernum = str.strip(decoder.decode_string(size=32).decode("ascii"))
        _LOGGER.debug("(read_rt_1) Version: %s", comm_version)
        _LOGGER.debug("(read_rt_1) Sernum: %s", comm_sernum)
        self.data["comm_version"] = comm_version.rstrip(' \t\r\n\0\u0000')
        self.data["comm_sernum"] = comm_sernum.rstrip(' \t\r\n\0\u0000')

        return True


    def read_sunspec_modbus_model_101_103(self):
        """Read SunSpec Model 101/103 Data"""
        # Max number of registers in one read for Modbus/TCP is 123
        # (ref.: https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251)
        #
        # So we could do 2 sweeps, one for M1 and the other for M103+M160. Since some old inverters have problems
        # with large sweeps, we'll split it in 3 sweeps:
        #   - Sweep 1 (M1): Start address 4 read 64 registers to read M1 (Common Inverter Info)
        #   - Sweep 2 (M103): Start address 70 read 40 registers to read M103+M160 (Realtime Power/Energy Data)
        #   - Sweep 3 (M160): Start address 124 read 40 registers to read M1 (Common Inverter Info)
        try:
            read_model_101_103_data = self.read_holding_registers(slave=self._slave_id, address=(self._base_addr + 70), count=40)
            _LOGGER.debug("(read_rt_101_103) Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_101_103) Base Address: %s", self._base_addr)
        except ModbusException:
            _LOGGER.debug("(read_rt_101_103) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_101_103) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_101_103_data.registers, byteorder=Endian.BIG
        )

        # register 70
        invtype = decoder.decode_16bit_uint()
        _LOGGER.debug("(read_rt_101_103) Inverter Type (int): %s", invtype)
        _LOGGER.debug("(read_rt_101_103) Inverter Type (str): %s", INVERTER_TYPE[invtype])
        # make sure the value is in the known status list
        if invtype not in INVERTER_TYPE:
            invtype = 999
            _LOGGER.debug("(read_rt_101_103) Inverter Type Unknown (int): %s", invtype)
            _LOGGER.debug("(read_rt_101_103) Inverter Type Unknown (str): %s", INVERTER_TYPE[invtype])
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
        # ensure that totalenergy is always an increasing value (total_increasing)
        _LOGGER.debug("(read_rt_101_103) Total Energy Value Read: %s", totalenergy)
        _LOGGER.debug("(read_rt_101_103) Total Energy Previous Value: %s", self.data["totalenergy"])
        if totalenergy < self.data["totalenergy"]:
            _LOGGER.error("(read_rt_101_103) Total Energy less than previous value! Value Read: %s - Previous Value: %s", totalenergy, self.data["totalenergy"])
        else:
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
        _LOGGER.debug("(read_rt_101_103) DC Power Value read: %s", self.data["dcpower"])
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
        _LOGGER.debug("(read_rt_101_103) Temp Cab Value read: %s", self.data["tempcab"])
        # register 108
        status = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if status not in DEVICE_STATUS:
            _LOGGER.debug("Unknown Operating State: %s", status)
            status = 999
        self.data["status"] = DEVICE_STATUS[status]
        _LOGGER.debug("(read_rt_101_103) Device Status Value read: %s", self.data["status"])

        # register 109
        statusvendor = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if statusvendor not in DEVICE_GLOBAL_STATUS:
            _LOGGER.debug("(init) Unknown Vendor Operating State: %s", statusvendor)
            statusvendor = 999
        self.data["statusvendor"] = DEVICE_GLOBAL_STATUS[statusvendor]
        _LOGGER.debug("(read_rt_101_103) Status Vendor Value read: %s", self.data["statusvendor"])
        _LOGGER.debug("(read_rt_101_103) Completed")
        return True


    def read_sunspec_modbus_model_160(self):
        """Read SunSpec Model 160 Data"""
        # Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 70 read 94 registers to read M103+M160 (Realtime Power/Energy Data) in 1-pass
        try:
            read_model_160_data = self.read_holding_registers(slave=self._slave_id, address=(self._base_addr + 122), count=42)
            _LOGGER.debug("(read_rt_160) Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_160) Base Address: %s", self._base_addr)
        except ModbusException:
            _LOGGER.debug("(read_rt_160) Reading data failed! Please check Slave ID: %s", self._slave_id)
            _LOGGER.debug("(read_rt_160) Reading data failed! Please check Reg. Base Address: %s", self._base_addr)
            return False

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_160_data.registers, byteorder=Endian.BIG
        )

        # register 122
        multi_mppt_id = decoder.decode_16bit_int()

        # skip register 123
        decoder.skip_bytes(2)

        # registers 124 to 126
        dcasf = decoder.decode_16bit_int()
        dcvsf = decoder.decode_16bit_int()
        dcwsf = decoder.decode_16bit_int()

        # skip register 127 to 129
        decoder.skip_bytes(6)

        # register 130 (# of DC modules)
        multi_mppt_nr = decoder.decode_16bit_int()

        if multi_mppt_id == 160:

            # if we have at least one DC module
            if multi_mppt_nr >= 1:

                # skip register 131 to 140
                decoder.skip_bytes(20)

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

            # if we have more than one DC module
            if multi_mppt_nr > 1:

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

        _LOGGER.debug("(read_rt_160) Completed")
        return True
