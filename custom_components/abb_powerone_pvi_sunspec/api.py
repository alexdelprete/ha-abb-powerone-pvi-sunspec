"""API Platform for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import logging
import socket
import threading

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.payload import BinaryPayloadDecoder

from .const import (
    DEVICE_GLOBAL_STATUS,
    DEVICE_MODEL,
    DEVICE_STATUS,
    INVERTER_TYPE,
    SUNSPEC_M160_OFFSETS,
    SUNSPEC_MODEL_160_ID,
)

_LOGGER = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Empty Error Class."""

    pass


class ModbusError(Exception):
    """Empty Error Class."""

    pass


class ABBPowerOneFimerAPI:
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
        """Initialize the Modbus API Client."""
        self._hass = hass
        self._name = name
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._base_addr = base_addr
        self._update_interval = scan_interval
        # Ensure ModBus Timeout is 1s less than scan_interval
        # https://github.com/binsentsu/home-assistant-solaredge-modbus/pull/183
        self._timeout = self._update_interval - 1
        self._client = ModbusTcpClient(
            host=self._host, port=self._port, timeout=self._timeout
        )
        self._lock = threading.Lock()
        self._sensors = []
        self.data = {}
        # Initialize ModBus data structure before first read
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
        self.data["mppt_nr"] = 1
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

    @property
    def name(self):
        """Return the device name."""
        return self._name

    @property
    def host(self):
        """Return the device name."""
        return self._host

    def check_port(self) -> bool:
        """Check if port is available."""
        with self._lock:
            sock_timeout = float(3)
            _LOGGER.debug(
                f"Check_Port: opening socket on {self._host}:{self._port} with a {sock_timeout}s timeout."
            )
            socket.setdefaulttimeout(sock_timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_res = sock.connect_ex((self._host, self._port))
            is_open = sock_res == 0  # True if open, False if not
            if is_open:
                sock.shutdown(socket.SHUT_RDWR)
                _LOGGER.debug(
                    f"Check_Port (SUCCESS): port open on {self._host}:{self._port}"
                )
            else:
                _LOGGER.debug(
                    f"Check_Port (ERROR): port not available on {self._host}:{self._port} - error: {sock_res}"
                )
            sock.close()
        return is_open

    def close(self):
        """Disconnect client."""
        try:
            if self._client.is_socket_open():
                _LOGGER.debug("Closing Modbus TCP connection")
                with self._lock:
                    self._client.close()
                    return True
            else:
                _LOGGER.debug("Modbus TCP connection already closed")
        except ConnectionException as connect_error:
            _LOGGER.debug(f"Close Connection connect_error: {connect_error}")
            raise ConnectionError() from connect_error

    def connect(self):
        """Connect client."""
        _LOGGER.debug(
            f"API Client connect to IP: {self._host} port: {self._port} slave id: {self._slave_id} timeout: {self._timeout}"
        )
        if self.check_port():
            _LOGGER.debug("Inverter ready for Modbus TCP connection")
            try:
                with self._lock:
                    self._client.connect()
                if not self._client.connected:
                    raise ConnectionError(
                        f"Failed to connect to {self._host}:{self._port} slave id {self._slave_id} timeout: {self._timeout}"
                    )
                else:
                    _LOGGER.debug("Modbus TCP Client connected")
                    return True
            except ModbusException:
                raise ConnectionError(
                    f"Failed to connect to {self._host}:{self._port} slave id {self._slave_id} timeout: {self._timeout}"
                )
        else:
            _LOGGER.debug("Inverter not ready for Modbus TCP connection")
            raise ConnectionError(f"Inverter not active on {self._host}:{self._port}")

    def read_holding_registers(self, slave, address, count):
        """Read holding registers."""
        kwargs = {"slave": slave} if slave else {}
        try:
            with self._lock:
                return self._client.read_holding_registers(address, count, **kwargs)
        except ConnectionException as connect_error:
            _LOGGER.debug(f"Read Holding Registers connect_error: {connect_error}")
            raise ConnectionError() from connect_error
        except ModbusException as modbus_error:
            _LOGGER.debug(f"Read Holding Registers modbus_error: {modbus_error}")
            raise ModbusError() from modbus_error

    def calculate_value(self, value, scalefactor):
        """Apply Scale Factor."""
        return value * 10**scalefactor

    async def async_get_data(self):
        """Read Data Function."""

        try:
            if self.connect():
                _LOGGER.debug(
                    f"Start Get data (Slave ID: {self._slave_id} - Base Address: {self._base_addr})"
                )
                # HA way to call a sync function from async function
                # https://developers.home-assistant.io/docs/asyncio_working_with_async?#calling-sync-functions-from-async
                result = await self._hass.async_add_executor_job(
                    self.read_sunspec_modbus
                )
                self.close()
                _LOGGER.debug("End Get data")
                if result:
                    _LOGGER.debug("Get Data Result: valid")
                    return True
                else:
                    _LOGGER.debug("Get Data Result: invalid")
                    return False
            else:
                _LOGGER.debug("Get Data failed: client not connected")
                return False
        except ConnectionException as connect_error:
            _LOGGER.debug(f"Async Get Data connect_error: {connect_error}")
            raise ConnectionError() from connect_error
        except ModbusException as modbus_error:
            _LOGGER.debug(f"Async Get Data modbus_error: {modbus_error}")
            raise ModbusError() from modbus_error

    def read_sunspec_modbus(self):
        """Read Modbus Data Function."""
        try:
            self.read_sunspec_modbus_model_1()
            self.read_sunspec_modbus_model_101_103()
            # Find SunSpec Model 160 Offset and read data only if found
            if offset := self.find_sunspec_modbus_m160_offset():
                self.read_sunspec_modbus_model_160(offset)
            result = True
            _LOGGER.debug(f"read_sunspec_modbus: success {result}")
        except Exception as modbus_error:
            _LOGGER.debug(f"read_sunspec_modbus: failed with error: {modbus_error}")
            result = False
            raise ModbusError() from modbus_error
        return result

    def find_sunspec_modbus_m160_offset(self) -> int:
        """Find SunSpec Model 160 Offset.

        This function attempts to find the offset for SunSpec Model 160 by trying different offsets.

        Returns:
            int: The found offset for SunSpec Model 160. Returns 0 if not found.

        Raises:
            ModbusError: If there is an error reading the Modbus registers.

        """
        try:
            # Model 160 default address: 40122 (or base address + 122)
            # For some inverters the offset is different, so we try 3 offsets
            invmodel = self.data["comm_model"].upper()
            found_offset = 0
            multi_mppt_id = 0
            for offset in SUNSPEC_M160_OFFSETS:
                _LOGGER.debug(
                    f"(find_m160) Find M160 for model: {invmodel} at offset: {offset}"
                )
                read_model_160_data = self.read_holding_registers(
                    slave=self._slave_id, address=(self._base_addr + offset), count=1
                )
                decoder = BinaryPayloadDecoder.fromRegisters(
                    read_model_160_data.registers, byteorder=Endian.BIG
                )
                multi_mppt_id = decoder.decode_16bit_uint()
                if multi_mppt_id != SUNSPEC_MODEL_160_ID:
                    _LOGGER.debug(
                        f"(find_m160) Model is not 160 - offset: {offset} - multi_mppt_id: {multi_mppt_id}"
                    )
                else:
                    _LOGGER.debug(
                        f"(find_m160) Model is 160 - offset: {offset} - multi_mppt_id: {multi_mppt_id}"
                    )
                    found_offset = offset
                    break
            if found_offset != 0:
                _LOGGER.debug(
                    f"(find_m160) Found M160 for model: {invmodel} at offset: {found_offset}"
                )
            else:
                _LOGGER.debug(f"(find_m160) M160 not found for model: {invmodel}")
            return found_offset
        except ModbusException as modbus_error:
            _LOGGER.debug(f"Find M160 modbus_error: {modbus_error}")
            raise ModbusError() from modbus_error

    def read_sunspec_modbus_model_1(self):
        """Read SunSpec Model 1 Data."""
        # A single register is 2 bytes. Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 72 read 92 registers to read (M101 or M103)+M160 (Realtime Power/Energy Data) in 1-pass
        try:
            read_model_1_data = self.read_holding_registers(
                slave=self._slave_id, address=(self._base_addr + 4), count=64
            )
            _LOGGER.debug(f"(read_rt_1) Slave ID: {self._slave_id}")
            _LOGGER.debug(f"(read_rt_1) Base Address: {self._base_addr}")
        except ModbusException as modbus_error:
            _LOGGER.debug(f"ReadM1 modbus_error: {modbus_error}")
            raise ModbusError() from modbus_error

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_1_data.registers, byteorder=Endian.BIG
        )

        # registers 4 to 43
        comm_manufact = str.strip(decoder.decode_string(size=32).decode("ascii"))
        comm_model = str.strip(decoder.decode_string(size=32).decode("ascii"))
        comm_options = str.strip(decoder.decode_string(size=16).decode("ascii"))
        self.data["comm_manufact"] = comm_manufact.rstrip(" \t\r\n\0\u0000")
        self.data["comm_model"] = comm_model.rstrip(" \t\r\n\0\u0000")
        self.data["comm_options"] = comm_options.rstrip(" \t\r\n\0\u0000")
        _LOGGER.debug(f"(read_rt_1) Manufacturer: {self.data['comm_manufact']}")
        _LOGGER.debug(f"(read_rt_1) Model: {self.data['comm_model']}")
        _LOGGER.debug(f"(read_rt_1) Options: {self.data['comm_options']}")

        # Model based on options register, if unknown, raise an error to report it
        # First char is the model: if non-printable char, hex string of the char is provided
        # So we need to check if it's a char or an hex value string and convert both to a number
        # Then we lookup in the model table, if it's there, good, otherwise we provide the given model
        # test also with opt_model = '0x0DED/0xFFFF'
        opt_model = self.data["comm_options"]
        if opt_model.startswith("0x"):
            opt_model_int = int(opt_model[0:4], 16)
            _LOGGER.debug(
                f"(opt_notprintable) opt_model: {opt_model} - opt_model_int: {opt_model_int}"
            )
        else:
            opt_model_int = ord(opt_model[0])
            _LOGGER.debug(
                f"(opt_printable) opt_model: {opt_model} - opt_model_int: {opt_model_int}"
            )
        if opt_model_int in DEVICE_MODEL:
            self.data["comm_model"] = DEVICE_MODEL[opt_model_int]
            _LOGGER.debug(f"(opt_comm_model) comm_model: {self.data['comm_model']}")
        else:
            _LOGGER.error(
                f"(opt_comm_model) Model unknown, report to @alexdelprete on the forum the following data: "
                f"Manuf.: {self.data['comm_manufact']} - Model: {self.data['comm_model']} - "
                f"Options: {self.data['comm_options']} - OptModel: {opt_model} - OptModelInt: {opt_model_int}"
            )

        # registers 44 to 67
        comm_version = str.strip(decoder.decode_string(size=16).decode("ascii"))
        comm_sernum = str.strip(decoder.decode_string(size=32).decode("ascii"))
        self.data["comm_version"] = comm_version.rstrip(" \t\r\n\0\u0000")
        self.data["comm_sernum"] = comm_sernum.rstrip(" \t\r\n\0\u0000")
        _LOGGER.debug(f"(read_rt_1) Version: {self.data['comm_version']}")
        _LOGGER.debug(f"(read_rt_1) Sernum: {self.data['comm_sernum']}")

        return True

    def read_sunspec_modbus_model_101_103(self):
        """Read SunSpec Model 101/103 Data."""

        # Max number of registers in one read for Modbus/TCP is 123
        # (ref.: https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251)
        #
        # So we could do 2 sweeps, one for M1 and the other for M103+M160. Since some old inverters have problems
        # with large sweeps, we'll split it in 3 sweeps:
        #   - Sweep 1 (M1): Start address 4 read 64 registers to read M1 (Common Inverter Info)
        #   - Sweep 2 (M103): Start address 70 read 40 registers to read M103+M160 (Realtime Power/Energy Data)
        #   - Sweep 3 (M160): Start address 124 read 40 registers to read M1 (Common Inverter Info)
        try:
            read_model_101_103_data = self.read_holding_registers(
                slave=self._slave_id, address=(self._base_addr + 70), count=40
            )
            _LOGGER.debug(f"(read_rt_101_103) Slave ID: {self._slave_id}")
            _LOGGER.debug(f"(read_rt_101_103) Base Address: {self._base_addr}")
        except ModbusException as modbus_error:
            _LOGGER.debug(
                f"(read_rt_101_103) Read M101/M103 modbus_error: {modbus_error}"
            )
            raise ModbusError() from modbus_error

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_101_103_data.registers, byteorder=Endian.BIG
        )

        # register 70
        invtype = decoder.decode_16bit_uint()
        _LOGGER.debug(f"(read_rt_101_103) Inverter Type (int): {invtype}")
        _LOGGER.debug(
            f"(read_rt_101_103) Inverter Type (str): {INVERTER_TYPE[invtype]}"
        )

        # make sure the value is in the known status list
        if invtype not in INVERTER_TYPE:
            invtype = 999
            _LOGGER.debug(f"(read_rt_101_103) Inverter Type Unknown (int): {invtype}")
            _LOGGER.debug(
                f"(read_rt_101_103) Inverter Type Unknown (str): {INVERTER_TYPE[invtype]}"
            )
        self.data["invtype"] = INVERTER_TYPE[invtype]

        # skip register 71
        decoder.skip_bytes(2)

        # registers 72 to 76
        accurrent = decoder.decode_16bit_uint()

        if invtype == 103:
            accurrenta = decoder.decode_16bit_uint()
            accurrentb = decoder.decode_16bit_uint()
            accurrentc = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(6)

        accurrentsf = decoder.decode_16bit_int()
        accurrent = self.calculate_value(accurrent, accurrentsf)
        self.data["accurrent"] = round(accurrent, abs(accurrentsf))

        if invtype == 103:
            accurrenta = self.calculate_value(accurrenta, accurrentsf)
            accurrentb = self.calculate_value(accurrentb, accurrentsf)
            accurrentc = self.calculate_value(accurrentc, accurrentsf)
            self.data["accurrenta"] = round(accurrenta, abs(accurrentsf))
            self.data["accurrentb"] = round(accurrentb, abs(accurrentsf))
            self.data["accurrentc"] = round(accurrentc, abs(accurrentsf))

        # registers 77 to 83
        if invtype == 103:
            acvoltageab = decoder.decode_16bit_uint()
            acvoltagebc = decoder.decode_16bit_uint()
            acvoltageca = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(6)

        acvoltagean = decoder.decode_16bit_uint()

        if invtype == 103:
            acvoltagebn = decoder.decode_16bit_uint()
            acvoltagecn = decoder.decode_16bit_uint()
        else:
            decoder.skip_bytes(4)

        acvoltagesf = decoder.decode_16bit_int()

        acvoltagean = self.calculate_value(acvoltagean, acvoltagesf)
        self.data["acvoltagean"] = round(acvoltagean, abs(acvoltagesf))

        if invtype == 103:
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
        _LOGGER.debug(f"(read_rt_101_103) Total Energy Value Read: {totalenergy}")
        _LOGGER.debug(
            f"(read_rt_101_103) Total Energy Previous Value: {self.data['totalenergy']}"
        )
        if totalenergy < self.data["totalenergy"]:
            _LOGGER.error(
                f"(read_rt_101_103) Total Energy less than previous value! Value Read: {totalenergy} - Previous Value: {self.data['totalenergy']}"
            )
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
            _LOGGER.debug(
                f"(read_rt_101_103) DC Current Value read: {self.data['dccurr']}"
            )
            _LOGGER.debug(
                f"(read_rt_101_103) DC Voltage Value read: {self.data['dcvolt']}"
            )
        else:
            decoder.skip_bytes(8)

        # registers 101 to 102
        dcpower = decoder.decode_16bit_int()
        dcpowersf = decoder.decode_16bit_int()
        dcpower = self.calculate_value(dcpower, dcpowersf)
        self.data["dcpower"] = round(dcpower, abs(dcpowersf))
        _LOGGER.debug(f"(read_rt_101_103) DC Power Value read: {self.data['dcpower']}")
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
        _LOGGER.debug(f"(read_rt_101_103) Temp Oth Value read: {self.data['tempoth']}")
        _LOGGER.debug(f"(read_rt_101_103) Temp Cab Value read: {self.data['tempcab']}")
        # register 108
        status = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if status not in DEVICE_STATUS:
            _LOGGER.debug(f"Unknown Operating State: {status}")
            status = 999
        self.data["status"] = DEVICE_STATUS[status]
        _LOGGER.debug(
            f"(read_rt_101_103) Device Status Value read: {self.data['status']}"
        )

        # register 109
        statusvendor = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if statusvendor not in DEVICE_GLOBAL_STATUS:
            _LOGGER.debug(
                f"(read_rt_101_103) Unknown Vendor Operating State: {statusvendor}"
            )
            statusvendor = 999
        self.data["statusvendor"] = DEVICE_GLOBAL_STATUS[statusvendor]
        _LOGGER.debug(
            f"(read_rt_101_103) Status Vendor Value read: {self.data['statusvendor']}"
        )
        _LOGGER.debug("(read_rt_101_103) Completed")
        return True

    def read_sunspec_modbus_model_160(self, offset=122):
        """Read SunSpec Model 160 Data."""
        # Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 70 read 94 registers to read M103+M160 (Realtime Power/Energy Data) in 1-pass

        try:
            # Model 160 default address: 40122 (or base address + 122)
            # For UNO-DM-PLUS/REACT2/TRIO inverters it has different offset
            invmodel = self.data["comm_model"].upper()
            _LOGGER.debug(f"(read_rt_160) Model: {invmodel}")
            _LOGGER.debug(f"(read_rt_160) Slave ID: {self._slave_id}")
            _LOGGER.debug(f"(read_rt_160) Base Address: {self._base_addr}")
            _LOGGER.debug(f"(read_rt_160) Offset: {offset}")
            read_model_160_data = self.read_holding_registers(
                slave=self._slave_id, address=(self._base_addr + offset), count=42
            )
        except ModbusException as modbus_error:
            _LOGGER.debug(f"Read M160 modbus_error: {modbus_error}")
            raise ModbusError() from modbus_error

        # No connection errors, we can start scraping registers
        decoder = BinaryPayloadDecoder.fromRegisters(
            read_model_160_data.registers, byteorder=Endian.BIG
        )

        # skip registers 122-123
        decoder.skip_bytes(4)

        # registers 124 to 126
        dcasf = decoder.decode_16bit_int()
        dcvsf = decoder.decode_16bit_int()
        dcwsf = decoder.decode_16bit_int()

        # skip register 127 to 129
        decoder.skip_bytes(6)

        # register 130 (# of DC modules)
        multi_mppt_nr = decoder.decode_16bit_int()
        self.data["mppt_nr"] = multi_mppt_nr
        _LOGGER.debug(f"(read_rt_160) mppt_nr {multi_mppt_nr}")

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
            # this fixes dcvolt -0.0 for UNO-DM/REACT2 models
            self.data["dcvolt"] = round(dc1volt, abs(dcvsf))
            dc1power = self.calculate_value(dc1power, dcwsf)
            self.data["dc1power"] = round(dc1power, abs(dcwsf))
            _LOGGER.debug(
                f"(read_rt_160) dc1curr: {dc1curr} Round: {self.data['dc1curr']} SF: {dcasf}"
            )
            _LOGGER.debug(f"(read_rt_160) dc1volt {self.data['dc1volt']}")
            _LOGGER.debug(f"(read_rt_160) dc1power {self.data['dc1power']}")

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
            _LOGGER.debug(
                f"(read_rt_160) dc2curr: {dc2curr} Round: {self.data['dc2curr']} SF: {dcasf}"
            )
            _LOGGER.debug(f"(read_rt_160) dc2volt {self.data['dc2volt']}")
            _LOGGER.debug(f"(read_rt_160) dc2power {self.data['dc2power']}")

        _LOGGER.debug("(read_rt_160) Completed")
        return True
