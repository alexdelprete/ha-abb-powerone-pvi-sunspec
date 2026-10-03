"""API Platform for ABB Power-One PVI SunSpec.

Reads the inverter over a unit on Home Assistant's shared Modbus connection
(``homeassistant.components.modbus``), so it can coexist with any other
integration talking to the same inverter or datalogger.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import logging
from typing import Any

from modbus_connection import ModbusError, ModbusExceptionError, ModbusProtocolError, ModbusUnit
from modbus_connection.decode import decode_int16, decode_string, decode_uint16, decode_uint32

from .const import (
    DEFAULT_CURRENT_VALUE,
    DEFAULT_ENERGY_VALUE,
    DEFAULT_FREQUENCY_VALUE,
    DEFAULT_M160_OFFSET_UNKNOWN,
    DEFAULT_MPPT_COUNT,
    DEFAULT_POWER_VALUE,
    DEFAULT_STRING_VALUE,
    DEFAULT_TEMPERATURE_VALUE,
    DEFAULT_VOLTAGE_VALUE,
    DEVICE_GLOBAL_STATUS,
    DEVICE_MODEL,
    DEVICE_STATUS,
    HEX_BASE,
    HEX_MODEL_SLICE_END,
    HEX_PREFIX,
    INVERTER_TYPE,
    SUNSPEC_M160_OFFSETS,
    SUNSPEC_MODEL_160_ID,
    TEMP_SCALE_FACTOR_CORRECTION,
    TEMP_THRESHOLD_CELSIUS,
)
from .helpers import log_debug, log_error

_LOGGER = logging.getLogger(__name__)

# M160 offset markers kept in data["m160_offset"] between polls
M160_NOT_PRESENT = 1

UNKNOWN_INVERTER_TYPE = 999
UNKNOWN_STATUS = 999
UNKNOWN_MODEL_OPTION = -1

# SunSpec "not implemented" values: a point carrying one has no reading
NOT_IMPLEMENTED_UINT16 = 0xFFFF
NOT_IMPLEMENTED_INT16 = -0x8000  # also the "not implemented" scale factor
NOT_IMPLEMENTED_UINT32 = 0xFFFFFFFF
NOT_IMPLEMENTED_ACC32 = 0


class _Registers:
    """Read values in order from a block of holding registers.

    Numeric reads return None for SunSpec's "not implemented" value.
    """

    def __init__(self, words: list[int]) -> None:
        """Start reading at the first register of the block."""
        self._words = words
        self._pos = 0

    def _take(self, count: int) -> list[int]:
        words = self._words[self._pos : self._pos + count]
        self._pos += count
        return words

    def skip(self, count: int) -> None:
        """Skip ``count`` registers."""
        self._pos += count

    def uint16(self) -> int | None:
        """Read one register as an unsigned 16-bit integer."""
        value = decode_uint16(self._take(1))
        return None if value == NOT_IMPLEMENTED_UINT16 else value

    def int16(self) -> int | None:
        """Read one register as a signed 16-bit integer (also a scale factor)."""
        value = decode_int16(self._take(1))
        return None if value == NOT_IMPLEMENTED_INT16 else value

    def acc32(self) -> int | None:
        """Read two registers as a SunSpec 32-bit accumulator."""
        value = decode_uint32(self._take(2))
        return None if value in (NOT_IMPLEMENTED_ACC32, NOT_IMPLEMENTED_UINT32) else value

    def string(self, count: int) -> str:
        """Read ``count`` registers as an ASCII string, padding stripped."""
        return decode_string(self._take(count)).strip()


class ABBPowerOneFimerAPI:
    """Client for ABB Power-One FIMER inverters using SunSpec Modbus.

    Supported models:
    - SunSpec Model 1: device identification
    - SunSpec Model 101/103: single-phase and three-phase inverter data
    - SunSpec Model 160: multiple MPPT string data, at an offset found on first read

    Requests on the shared connection are serialized by Home Assistant, and the
    connection is opened on the first request and re-opened on the next request
    after it drops. Errors are raised as ``modbus_connection.ModbusError``; a
    reading the inverter does not implement is stored as None.
    """

    data: dict[str, Any]

    def __init__(self, name: str, host: str, unit: ModbusUnit, base_addr: int) -> None:
        """Initialize the API client.

        Args:
            name: Device name
            host: Device host, for the device's configuration URL
            unit: Modbus unit of the inverter on the shared connection
            base_addr: SunSpec base address (0 or 40000)

        """
        self._name = str(name)
        self._host = str(host)
        self._unit = unit
        self._base_addr = int(base_addr)
        # Model 1 is static: read it once, and again after any failed poll
        self._device_info_cached = False
        self.data = {}
        self._initialize_data_structure()

    def _initialize_data_structure(self) -> None:
        """Set default values for every data point before the first read."""
        # AC current measurements
        self.data["accurrent"] = DEFAULT_CURRENT_VALUE
        self.data["accurrenta"] = DEFAULT_CURRENT_VALUE
        self.data["accurrentb"] = DEFAULT_CURRENT_VALUE
        self.data["accurrentc"] = DEFAULT_CURRENT_VALUE

        # AC voltage measurements
        self.data["acvoltageab"] = DEFAULT_VOLTAGE_VALUE
        self.data["acvoltagebc"] = DEFAULT_VOLTAGE_VALUE
        self.data["acvoltageca"] = DEFAULT_VOLTAGE_VALUE
        self.data["acvoltagean"] = DEFAULT_VOLTAGE_VALUE
        self.data["acvoltagebn"] = DEFAULT_VOLTAGE_VALUE
        self.data["acvoltagecn"] = DEFAULT_VOLTAGE_VALUE

        # AC power and frequency
        self.data["acpower"] = DEFAULT_POWER_VALUE
        self.data["acfreq"] = DEFAULT_FREQUENCY_VALUE

        # Communication/identification data
        self.data["comm_options"] = DEFAULT_CURRENT_VALUE
        self.data["comm_manufact"] = DEFAULT_STRING_VALUE
        self.data["comm_model"] = DEFAULT_STRING_VALUE
        self.data["comm_version"] = DEFAULT_STRING_VALUE
        self.data["comm_sernum"] = DEFAULT_STRING_VALUE

        # MPPT and DC measurements
        self.data["mppt_nr"] = DEFAULT_MPPT_COUNT
        self.data["dccurr"] = DEFAULT_CURRENT_VALUE
        self.data["dcvolt"] = DEFAULT_VOLTAGE_VALUE
        self.data["dcpower"] = DEFAULT_POWER_VALUE
        self.data["dc1curr"] = DEFAULT_CURRENT_VALUE
        self.data["dc1volt"] = DEFAULT_VOLTAGE_VALUE
        self.data["dc1power"] = DEFAULT_POWER_VALUE
        self.data["dc2curr"] = DEFAULT_CURRENT_VALUE
        self.data["dc2volt"] = DEFAULT_VOLTAGE_VALUE
        self.data["dc2power"] = DEFAULT_POWER_VALUE

        # Status and operation data
        self.data["invtype"] = DEFAULT_STRING_VALUE
        self.data["status"] = DEFAULT_STRING_VALUE
        self.data["statusvendor"] = DEFAULT_STRING_VALUE
        self.data["totalenergy"] = DEFAULT_ENERGY_VALUE
        self.data["tempcab"] = DEFAULT_TEMPERATURE_VALUE
        self.data["tempoth"] = DEFAULT_TEMPERATURE_VALUE

        # Internal state tracking (not modbus data)
        self.data["m160_offset"] = DEFAULT_M160_OFFSET_UNKNOWN

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def host(self) -> str:
        """Return the device host."""
        return self._host

    async def _read(self, offset: int, count: int) -> _Registers:
        """Read ``count`` holding registers at ``offset`` from the base address.

        Raises:
            ModbusProtocolError: the inverter answered with a different number of registers

        """
        address = self._base_addr + offset
        words = await self._unit.read_holding_registers(address, count)
        if len(words) != count:
            raise ModbusProtocolError(
                f"Read of {count} registers at {address} returned {len(words)}"
            )
        return _Registers(words)

    def calculate_value(self, value: float | None, sf: int | None) -> float | None:
        """Apply Scale Factor and round the result; None if either is not implemented."""
        if value is None or sf is None:
            return None
        return round(value * 10**sf, max(0, -sf))

    def _parse_model_options(self, options_string: str) -> int:
        """Return the model number encoded in the first character of the options string.

        A non-printable character is reported as a hex string (e.g. ``0x0D``).
        """
        if not options_string:
            return UNKNOWN_MODEL_OPTION
        if options_string.lower().startswith(HEX_PREFIX):
            try:
                return int(options_string[0:HEX_MODEL_SLICE_END], HEX_BASE)
            except ValueError:
                return UNKNOWN_MODEL_OPTION
        return ord(options_string[0])

    def _apply_temperature_correction(
        self, temp_value: int | None, temp_sf: int | None
    ) -> float | None:
        """Apply temperature correction for cabinet temperature.

        In some inverters, the scale factor must be -2 instead of -1 as per specs.
        """
        temp_corrected = self.calculate_value(temp_value, temp_sf)
        if temp_corrected is not None and temp_corrected > TEMP_THRESHOLD_CELSIUS:
            temp_corrected = self.calculate_value(temp_value, TEMP_SCALE_FACTOR_CORRECTION)
        return temp_corrected

    async def async_get_data(self) -> dict[str, Any]:
        """Read all supported SunSpec models and return the updated data.

        Raises:
            ModbusError: the inverter could not be reached, refused a read or answered garbage
            OSError: a transport error the Modbus library did not wrap

        """
        try:
            await self.read_sunspec_modbus()
        except ModbusError, OSError:
            # re-read the device info once the inverter answers again
            self._device_info_cached = False
            raise
        log_debug(_LOGGER, "async_get_data", "Data read successful")
        return self.data

    async def read_sunspec_modbus(self) -> None:
        """Read Model 1 (when needed), Model 101/103 and Model 160."""
        if not self._device_info_cached:
            await self.read_sunspec_modbus_model_1()
            self._device_info_cached = True

        await self.read_sunspec_modbus_model_101_103()

        offset = self.data["m160_offset"]
        if offset == DEFAULT_M160_OFFSET_UNKNOWN:
            # look for M160 only once: remember the offset, or that there is none
            if offset := await self.find_sunspec_modbus_m160_offset():
                await self.read_sunspec_modbus_model_160(offset)
                self.data["m160_offset"] = offset
            else:
                self.data["m160_offset"] = M160_NOT_PRESENT
        elif offset != M160_NOT_PRESENT:
            await self.read_sunspec_modbus_model_160(offset)
        log_debug(
            _LOGGER,
            "read_sunspec_modbus",
            "Completed",
            model=self.data["comm_model"],
            m160_offset=self.data["m160_offset"],
        )

    async def find_sunspec_modbus_m160_offset(self) -> int:
        """Return the offset of SunSpec Model 160, or 0 if the inverter has none.

        The model usually starts at base address + 122, but some inverters place
        it elsewhere, so every known offset is tried in turn. An offset the
        inverter refuses is skipped; any other error fails the poll, and the
        search runs again on the next one.
        """
        for offset in SUNSPEC_M160_OFFSETS:
            try:
                model_id = (await self._read(offset, 1)).uint16()
            except ModbusExceptionError as err:
                # the inverter has no register there: try the next offset
                log_debug(
                    _LOGGER,
                    "find_sunspec_modbus_m160_offset",
                    "Modbus exception response",
                    offset=offset,
                    error=err,
                )
                continue
            if model_id == SUNSPEC_MODEL_160_ID:
                log_debug(_LOGGER, "find_sunspec_modbus_m160_offset", "M160 found", offset=offset)
                return offset
        log_debug(
            _LOGGER,
            "find_sunspec_modbus_m160_offset",
            "M160 not found",
            model=self.data["comm_model"],
        )
        return 0

    async def read_sunspec_modbus_model_1(self) -> None:
        """Read SunSpec Model 1 (common block), registers 4 to 67."""
        regs = await self._read(4, 64)

        # registers 4 to 43
        self.data["comm_manufact"] = regs.string(16)
        self.data["comm_model"] = regs.string(16)
        self.data["comm_options"] = regs.string(8)

        # The first char of the options register is the model: look it up in the
        # model table, and fall back to the model register when it is not there
        opt_model = self.data["comm_options"]
        opt_model_int = self._parse_model_options(opt_model)
        if opt_model_int in DEVICE_MODEL:
            self.data["comm_model"] = DEVICE_MODEL[opt_model_int]
        else:
            log_error(
                _LOGGER,
                "read_sunspec_modbus_model_1",
                "Model unknown, report to @alexdelprete on the forum the following data",
                manufacturer=self.data["comm_manufact"],
                model=self.data["comm_model"],
                options=opt_model,
                opt_model_int=opt_model_int,
            )

        # registers 44 to 67
        self.data["comm_version"] = regs.string(8)
        self.data["comm_sernum"] = regs.string(16)
        log_debug(
            _LOGGER,
            "read_sunspec_modbus_model_1",
            "Device info read",
            manufacturer=self.data["comm_manufact"],
            model=self.data["comm_model"],
            options=opt_model,
            version=self.data["comm_version"],
            serial=self.data["comm_sernum"],
        )

    async def read_sunspec_modbus_model_101_103(self) -> None:
        """Read SunSpec Model 101/103 (inverter), registers 70 to 109."""
        regs = await self._read(70, 40)

        # register 70
        invtype = regs.uint16()
        if invtype not in INVERTER_TYPE:
            log_debug(
                _LOGGER,
                "read_sunspec_modbus_model_101_103",
                "Inverter type unknown",
                invtype_int=invtype,
            )
            invtype = UNKNOWN_INVERTER_TYPE
        self.data["invtype"] = INVERTER_TYPE[invtype]
        three_phase = invtype == 103

        # skip register 71
        regs.skip(1)

        # registers 72 to 76
        accurrent = regs.uint16()
        if three_phase:
            accurrenta = regs.uint16()
            accurrentb = regs.uint16()
            accurrentc = regs.uint16()
        else:
            regs.skip(3)
        accurrentsf = regs.int16()
        self.data["accurrent"] = self.calculate_value(accurrent, accurrentsf)
        if three_phase:
            self.data["accurrenta"] = self.calculate_value(accurrenta, accurrentsf)
            self.data["accurrentb"] = self.calculate_value(accurrentb, accurrentsf)
            self.data["accurrentc"] = self.calculate_value(accurrentc, accurrentsf)

        # registers 77 to 83
        if three_phase:
            acvoltageab = regs.uint16()
            acvoltagebc = regs.uint16()
            acvoltageca = regs.uint16()
        else:
            regs.skip(3)
        acvoltagean = regs.uint16()
        if three_phase:
            acvoltagebn = regs.uint16()
            acvoltagecn = regs.uint16()
        else:
            regs.skip(2)
        acvoltagesf = regs.int16()
        self.data["acvoltagean"] = self.calculate_value(acvoltagean, acvoltagesf)
        if three_phase:
            self.data["acvoltageab"] = self.calculate_value(acvoltageab, acvoltagesf)
            self.data["acvoltagebc"] = self.calculate_value(acvoltagebc, acvoltagesf)
            self.data["acvoltageca"] = self.calculate_value(acvoltageca, acvoltagesf)
            self.data["acvoltagebn"] = self.calculate_value(acvoltagebn, acvoltagesf)
            self.data["acvoltagecn"] = self.calculate_value(acvoltagecn, acvoltagesf)

        # registers 84 to 85
        acpower = regs.int16()
        self.data["acpower"] = self.calculate_value(acpower, regs.int16())

        # registers 86 to 87
        acfreq = regs.uint16()
        self.data["acfreq"] = self.calculate_value(acfreq, regs.int16())

        # skip registers 88 to 93
        regs.skip(6)

        # registers 94 to 96
        totalenergy = regs.acc32()
        totalenergy = self.calculate_value(totalenergy, regs.int16())
        # totalenergy is total_increasing: keep the last reading when there is
        # none, and never let it go backwards
        if totalenergy is None:
            log_debug(_LOGGER, "read_sunspec_modbus_model_101_103", "Total energy not available")
        elif totalenergy < self.data["totalenergy"]:
            log_error(
                _LOGGER,
                "read_sunspec_modbus_model_101_103",
                "Total Energy less than previous value!",
                value_read=totalenergy,
                previous_value=self.data["totalenergy"],
            )
        else:
            self.data["totalenergy"] = totalenergy

        # registers 97 to 100 (single-phase inverters only)
        if invtype == 101:
            dccurr = regs.int16()
            dccurrsf = regs.int16()
            dcvolt = regs.int16()
            dcvoltsf = regs.int16()
            self.data["dccurr"] = self.calculate_value(dccurr, dccurrsf)
            self.data["dcvolt"] = self.calculate_value(dcvolt, dcvoltsf)
        else:
            regs.skip(4)

        # registers 101 to 102
        dcpower = regs.int16()
        self.data["dcpower"] = self.calculate_value(dcpower, regs.int16())

        # register 103, skip 104 to 105, registers 106 to 107
        tempcab = regs.int16()
        regs.skip(2)
        tempoth = regs.int16()
        tempsf = regs.int16()
        # in some inverters the cabinet temperature SF must be -2, not -1 as per specs
        self.data["tempcab"] = self._apply_temperature_correction(tempcab, tempsf)
        self.data["tempoth"] = self.calculate_value(tempoth, tempsf)

        # register 108: SunSpec operating state (enum16)
        status = regs.uint16()
        if status not in DEVICE_STATUS:
            log_debug(_LOGGER, "read_sunspec_modbus_model_101_103", "Unknown status", status=status)
            status = UNKNOWN_STATUS
        self.data["status"] = DEVICE_STATUS[status]

        # register 109: ABB/FIMER global state (Aurora)
        statusvendor = regs.int16()
        if statusvendor not in DEVICE_GLOBAL_STATUS:
            log_debug(
                _LOGGER,
                "read_sunspec_modbus_model_101_103",
                "Unknown vendor status",
                statusvendor=statusvendor,
            )
            statusvendor = UNKNOWN_STATUS
        self.data["statusvendor"] = DEVICE_GLOBAL_STATUS[statusvendor]
        log_debug(
            _LOGGER,
            "read_sunspec_modbus_model_101_103",
            "Completed",
            invtype=self.data["invtype"],
            acpower=self.data["acpower"],
            status=self.data["status"],
        )

    async def read_sunspec_modbus_model_160(self, offset: int = 122) -> None:
        """Read SunSpec Model 160 (multiple MPPT) at ``offset``, 42 registers."""
        regs = await self._read(offset, 42)

        # skip model ID and length, then the current, voltage and power scale factors
        regs.skip(2)
        dcasf = regs.int16()
        dcvsf = regs.int16()
        dcwsf = regs.int16()

        # skip energy scale factor and events, then the number of DC modules
        regs.skip(3)
        multi_mppt_nr = regs.int16() or 0
        self.data["mppt_nr"] = multi_mppt_nr

        if multi_mppt_nr >= 1:
            # skip timestamp period, module ID and ID string
            regs.skip(10)
            dc1curr = regs.uint16()
            dc1volt = regs.uint16()
            dc1power = regs.uint16()
            self.data["dc1curr"] = self.calculate_value(dc1curr, dcasf)
            self.data["dc1volt"] = self.calculate_value(dc1volt, dcvsf)
            # this fixes dcvolt -0.0 for UNO-DM/REACT2 models
            self.data["dcvolt"] = self.data["dc1volt"]
            self.data["dc1power"] = self.calculate_value(dc1power, dcwsf)

        if multi_mppt_nr > 1:
            # skip the rest of module 1, then module 2's ID and ID string
            regs.skip(17)
            dc2curr = regs.uint16()
            dc2volt = regs.uint16()
            dc2power = regs.uint16()
            self.data["dc2curr"] = self.calculate_value(dc2curr, dcasf)
            self.data["dc2volt"] = self.calculate_value(dc2volt, dcvsf)
            self.data["dc2power"] = self.calculate_value(dc2power, dcwsf)

        log_debug(
            _LOGGER,
            "read_sunspec_modbus_model_160",
            "Completed",
            mppt_count=multi_mppt_nr,
            dc1_power=self.data["dc1power"],
            dc2_power=self.data["dc2power"],
        )
