"""API Platform for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import asyncio
import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from pymodbus import ExceptionResponse
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException

from .const import (
    DEFAULT_CURRENT_VALUE,
    DEFAULT_ENERGY_VALUE,
    DEFAULT_FREQUENCY_VALUE,
    DEFAULT_M160_OFFSET_UNKNOWN,
    DEFAULT_MPPT_COUNT,
    DEFAULT_POWER_VALUE,
    DEFAULT_SOCKET_TIMEOUT,
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
    MAX_BASE_ADDR,
    MAX_PORT,
    MAX_SCAN_INTERVAL,
    MAX_SLAVE_ID,
    MIN_BASE_ADDR,
    MIN_PORT,
    MIN_SCAN_INTERVAL,
    MIN_SLAVE_ID,
    MIN_TIMEOUT_BUFFER,
    SUNSPEC_M160_OFFSETS,
    SUNSPEC_MODEL_160_ID,
    TEMP_SCALE_FACTOR_CORRECTION,
    TEMP_THRESHOLD_CELSIUS,
)
from .pymodbus_constants import Endian
from .pymodbus_payload import BinaryPayloadDecoder

_LOGGER = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Exception raised when connection to the inverter fails.

    This exception is raised when the client cannot establish or maintain
    a connection to the inverter's Modbus TCP interface.

    Args:
        message: Human readable error message
        host: The inverter's IP address or hostname
        port: The Modbus TCP port number
        slave_id: The Modbus slave ID
        timeout: Connection timeout in seconds

    """

    def __init__(
        self,
        message: str = "Connection failed",
        host: str | None = None,
        port: int | None = None,
        slave_id: int | None = None,
        timeout: int | None = None,
    ):
        """Initialize ConnectionError exception."""
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.timeout = timeout
        if host and port:
            message = f"{message} (host: {host}, port: {port})"
        super().__init__(message)


class ModbusError(Exception):
    """Exception raised when Modbus protocol errors occur.

    This exception is raised when there are errors in the Modbus protocol
    communication, such as invalid register addresses, communication timeouts,
    or protocol-specific errors.

    Args:
        message: Human readable error message
        function_code: Modbus function code that caused the error
        register_address: Starting register address
        register_count: Number of registers involved

    """

    def __init__(
        self,
        message: str = "Modbus protocol error",
        function_code: int | None = None,
        register_address: int | None = None,
        register_count: int | None = None,
    ):
        """Initialize ModbusError exception."""
        self.function_code = function_code
        self.register_address = register_address
        self.register_count = register_count
        if register_address:
            message = f"{message} (register: {register_address})"
        super().__init__(message)


class ExceptionError(Exception):
    """Exception raised for unexpected errors during operation.

    This exception is raised when unexpected errors occur that don't fall
    into the connection or Modbus protocol error categories.

    Args:
        message: Human readable error message
        operation: The operation that was being performed when the error occurred

    """

    def __init__(
        self, message: str = "Unexpected error occurred", operation: str | None = None
    ):
        """Initialize ExceptionError exception."""
        self.operation = operation
        if operation:
            message = f"{message} (during: {operation})"
        super().__init__(message)


class ABBPowerOneFimerAPI:
    """Thread-safe API client for ABB Power-One Fimer inverters using SunSpec Modbus.

    This class provides a complete interface for communicating with ABB Power-One
    inverters via Modbus TCP using the SunSpec protocol specification. It handles
    connection management, data collection, and provides a consistent interface
    for Home Assistant integration.

    Supported Features:
    - SunSpec Model 1: Device identification and common information
    - SunSpec Model 101/103: Single-phase and three-phase inverter data
    - SunSpec Model 160: Multiple MPPT string data
    - Automatic model detection and offset discovery
    - Connection health monitoring and error recovery
    - Thread-safe operation with asyncio locks

    Attributes:
        data: Dictionary containing all inverter data points

    Example:
        api = ABBPowerOneFimerAPI(
            hass=hass,
            name="Inverter 1",
            host="192.168.1.100",
            port=502,
            slave_id=1,
            base_addr=40000,
            scan_interval=30
        )

        if await api.async_get_data():
            power = api.data['acpower']
            energy = api.data['totalenergy']

    """

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: int,
        slave_id: int,
        base_addr: int,
        scan_interval: int,
    ) -> None:
        """Initialize the Modbus API Client.

        Args:
            hass: HomeAssistant instance
            name: Device name
            host: Device IP address
            port: Modbus TCP port
            slave_id: Modbus slave ID (1-247)
            base_addr: Base address for register reads
            scan_interval: Update interval in seconds

        """
        self._hass = hass
        self._name = str(name)
        self._host = str(host)

        # Validate and set configuration parameters
        self._port = self._validate_port(int(port))
        self._slave_id = self._validate_slave_id(int(slave_id))
        self._base_addr = self._validate_base_addr(int(base_addr))
        self._update_interval = self._validate_scan_interval(int(scan_interval))
        # Ensure ModBus Timeout is 1s less than scan_interval
        # https://github.com/binsentsu/home-assistant-solaredge-modbus/pull/183
        self._timeout = self._update_interval - MIN_TIMEOUT_BUFFER
        self._client = AsyncModbusTcpClient(
            host=self._host, port=self._port, timeout=self._timeout
        )
        self._lock = asyncio.Lock()
        self._sensors = []
        self.data: dict[str, Any] = {}
        self._connection_healthy = False
        self._last_successful_read = None
        # Performance optimization: cache device info after first read
        self._device_info_cached = False
        self._initialize_data_structure()

    def _initialize_data_structure(self) -> None:
        """Initialize the data structure with default values.

        This method sets up the data dictionary with default values for all
        expected inverter data points. This ensures consistent data structure
        before the first actual read from the inverter.
        """
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

    def _validate_port(self, port: int) -> int:
        """Validate TCP port number.

        Args:
            port: Port number to validate

        Returns:
            int: Validated port number

        Raises:
            ValueError: If port is out of valid range

        """
        if not (MIN_PORT <= port <= MAX_PORT):
            raise ValueError(
                f"Port must be between {MIN_PORT} and {MAX_PORT}, got {port}"
            )
        return port

    def _validate_slave_id(self, slave_id: int) -> int:
        """Validate Modbus slave ID.

        Args:
            slave_id: Slave ID to validate

        Returns:
            int: Validated slave ID

        Raises:
            ValueError: If slave ID is out of valid range

        """
        if not (MIN_SLAVE_ID <= slave_id <= MAX_SLAVE_ID):
            raise ValueError(
                f"Slave ID must be between {MIN_SLAVE_ID} and {MAX_SLAVE_ID}, got {slave_id}"
            )
        return slave_id

    def _validate_base_addr(self, base_addr: int) -> int:
        """Validate base address.

        Args:
            base_addr: Base address to validate

        Returns:
            int: Validated base address

        Raises:
            ValueError: If base address is out of valid range

        """
        if not (MIN_BASE_ADDR <= base_addr <= MAX_BASE_ADDR):
            raise ValueError(
                f"Base address must be between {MIN_BASE_ADDR} and {MAX_BASE_ADDR}, got {base_addr}"
            )
        return base_addr

    def _validate_scan_interval(self, scan_interval: int) -> int:
        """Validate scan interval.

        Args:
            scan_interval: Scan interval to validate

        Returns:
            int: Validated scan interval

        Raises:
            ValueError: If scan interval is out of valid range

        """
        if not (MIN_SCAN_INTERVAL <= scan_interval <= MAX_SCAN_INTERVAL):
            raise ValueError(
                f"Scan interval must be between {MIN_SCAN_INTERVAL} and {MAX_SCAN_INTERVAL}, got {scan_interval}"
            )
        return scan_interval

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def host(self) -> str:
        """Return the device host."""
        return self._host

    async def check_port(self) -> bool:
        """Check if the inverter port is available and responsive.

        This method performs a basic TCP connection test to verify that
        the inverter is reachable on the specified host and port before
        attempting Modbus communication.

        Returns:
            bool: True if port is open and responsive, False otherwise

        """
        async with self._lock:
            sock_timeout = DEFAULT_SOCKET_TIMEOUT
            self._log_debug(
                "check_port",
                f"Opening socket with {sock_timeout}s timeout",
                host=self._host,
                port=self._port,
            )
            try:
                # Use asyncio to check port availability
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(self._host, self._port),
                    timeout=sock_timeout,
                )
                writer.close()
                await writer.wait_closed()
                self._log_debug(
                    "check_port",
                    "Port connection successful",
                    host=self._host,
                    port=self._port,
                )
                return True
            except (asyncio.TimeoutError, OSError) as e:  # noqa: UP041
                self._log_debug(
                    "check_port",
                    f"Port not available - {e}",
                    host=self._host,
                    port=self._port,
                )
                return False

    async def close(self) -> bool | None:
        """Safely disconnect the Modbus client.

        Closes the active Modbus TCP connection and cleans up resources.
        This method is thread-safe and handles connection state checking.

        Returns:
            Optional[bool]: True if successfully closed, None if already closed

        Raises:
            ConnectionError: If there's an error during the close operation

        """
        try:
            if self._client.connected:
                self._log_debug("close", "Closing Modbus TCP connection")
                async with self._lock:
                    self._client.close()
                    return True
            else:
                self._log_debug("close", "Modbus TCP connection already closed")
        except ConnectionException as connect_error:
            self._log_debug("close", f"Connection error: {connect_error}")
            raise ConnectionError(
                "Failed to close connection",
                host=self._host,
                port=self._port,
                slave_id=self._slave_id,
            ) from connect_error

    async def connect(self) -> bool:
        """Connect client."""
        self._log_debug(
            "connect",
            "API Client connecting",
            host=self._host,
            port=self._port,
            slave_id=self._slave_id,
            timeout=self._timeout,
        )
        if await self.check_port():
            self._log_debug("connect", "Inverter ready for Modbus TCP connection")
            try:
                async with self._lock:
                    await self._client.connect()
                if not self._client.connected:
                    raise ConnectionError(
                        "Failed to establish connection",
                        host=self._host,
                        port=self._port,
                        slave_id=self._slave_id,
                        timeout=self._timeout,
                    )
                self._log_debug("connect", "Modbus TCP Client connected")
                return True
            except ModbusException as modbus_error:
                raise ConnectionError(
                    "Modbus connection failed",
                    host=self._host,
                    port=self._port,
                    slave_id=self._slave_id,
                    timeout=self._timeout,
                ) from modbus_error
        else:
            self._log_debug("connect", "Inverter not ready for Modbus TCP connection")
            raise ConnectionError(
                "Inverter not responding", host=self._host, port=self._port
            )

    async def read_holding_registers(self, address: int, count: int) -> Any:
        """Read holding registers."""

        try:
            async with self._lock:
                return await self._client.read_holding_registers(
                    address=address, count=count, slave=self._slave_id
                )  # type: ignore (pylance thinks this is not awaitable)
        except ConnectionException as connect_error:
            self._log_debug(
                "read_holding_registers", f"Connection error: {connect_error}"
            )
            raise ConnectionError(
                "Connection lost during register read",
                host=self._host,
                port=self._port,
                slave_id=self._slave_id,
            ) from connect_error
        except ModbusException as modbus_error:
            self._log_debug("read_holding_registers", f"Modbus error: {modbus_error}")
            raise ModbusError(
                "Failed to read registers",
                register_address=address,
                register_count=count,
            ) from modbus_error

    def calculate_value(self, value: float, sf: int) -> float:
        """Apply Scale Factor and round the result."""
        return round(value * 10**sf, max(0, -sf))

    def _clean_string(self, raw_string: str) -> str:
        """Clean and process string values from Modbus registers.

        This method handles the common string cleaning operations for
        strings decoded from Modbus registers, including removing
        null bytes, whitespace, and other control characters.

        Args:
            raw_string: The raw string decoded from Modbus registers

        Returns:
            str: Cleaned string with unwanted characters removed

        Raises:
            ExceptionError: If string processing fails

        """
        try:
            # Strip whitespace and common control characters
            cleaned = raw_string.strip()
            # Remove null bytes and other control characters
            cleaned = cleaned.rstrip(" \t\r\n\0\u0000")
            return cleaned
        except (AttributeError, UnicodeError) as e:
            self._log_warning(
                "_clean_string", f"Failed to clean string: {e}", raw_string=raw_string
            )
            raise ExceptionError(
                f"String processing failed: {e}", operation="string_cleaning"
            ) from e

    def _parse_model_options(self, options_string: str) -> int:
        """Parse model options string to extract model integer.

        Args:
            options_string: The options string from the inverter

        Returns:
            int: The parsed model integer

        """
        if options_string.startswith(HEX_PREFIX):
            opt_model_int = int(options_string[0:HEX_MODEL_SLICE_END], HEX_BASE)
            self._log_debug(
                "_parse_model_options",
                "Non-printable option model",
                options_string=options_string,
                opt_model_int=opt_model_int,
            )
        else:
            opt_model_int = ord(options_string[0])
            self._log_debug(
                "_parse_model_options",
                "Printable option model",
                options_string=options_string,
                opt_model_int=opt_model_int,
            )
        return opt_model_int

    def _apply_temperature_correction(self, temp_value: int, temp_sf: int) -> float:
        """Apply temperature correction for cabinet temperature.

        In some inverters, the scale factor must be -2 instead of -1 as per specs.

        Args:
            temp_value: Raw temperature value
            temp_sf: Temperature scale factor

        Returns:
            int: Corrected temperature value

        """
        temp_corrected = self.calculate_value(temp_value, temp_sf)
        if temp_corrected > TEMP_THRESHOLD_CELSIUS:
            temp_corrected = self.calculate_value(
                temp_value, TEMP_SCALE_FACTOR_CORRECTION
            )
        return temp_corrected

    def _log_debug(self, method: str, message: str, **kwargs) -> None:
        """Standardized debug logging with method context.

        Args:
            method: The method name for context
            message: The log message
            **kwargs: Additional context data to include

        """
        context_str = f"({method})"
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str += f" [{', '.join(context_parts)}]"
        _LOGGER.debug(f"{context_str}: {message}")

    def _log_warning(self, method: str, message: str, **kwargs) -> None:
        """Standardized warning logging with method context.

        Args:
            method: The method name for context
            message: The warning message
            **kwargs: Additional context data to include

        """
        context_str = f"({method})"
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str += f" [{', '.join(context_parts)}]"
        _LOGGER.warning(f"{context_str}: {message}")

    def _log_error(self, method: str, message: str, **kwargs) -> None:
        """Standardized error logging with method context.

        Args:
            method: The method name for context
            message: The error message
            **kwargs: Additional context data to include

        """
        context_str = f"({method})"
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str += f" [{', '.join(context_parts)}]"
        _LOGGER.error(f"{context_str}: {message}")

    def is_connection_healthy(self) -> bool:
        """Check if the connection is healthy.

        Returns:
            bool: True if connection is healthy, False otherwise

        """
        return self._connection_healthy and self._client.connected

    def _mark_connection_healthy(self) -> None:
        """Mark connection as healthy after successful operation."""
        self._connection_healthy = True
        self._last_successful_read = datetime.datetime.now()

    def _mark_connection_unhealthy(self) -> None:
        """Mark connection as unhealthy after failed operation."""
        self._connection_healthy = False

    def _should_read_device_info(self) -> bool:
        """Check if device information should be read.

        Device info (Model 1) is relatively static and only needs to be
        read once during initialization or after connection issues.

        Returns:
            bool: True if device info should be read

        """
        return not self._device_info_cached or not self._connection_healthy

    async def async_get_data(self) -> bool:
        """Collect inverter information data.

        This method orchestrates the complete data collection process:
        1. Establishes connection to the inverter
        2. Reads all supported SunSpec models (1, 101/103, 160)
        3. Updates the data dictionary with current values
        4. Manages connection health status
        5. Properly closes the connection

        Returns:
            bool: True if data collection was successful, False otherwise

        Raises:
            ConnectionError: If connection to inverter fails
            ModbusError: If Modbus protocol errors occur

        """

        try:
            if await self.connect():
                self._log_debug(
                    "async_get_data",
                    "Starting data collection",
                    slave_id=self._slave_id,
                    base_addr=self._base_addr,
                )
                # HA way to call a sync function from async function
                # https://developers.home-assistant.io/docs/asyncio_working_with_async?#calling-sync-functions-from-async
                result = await self.read_sunspec_modbus()
                await self.close()
                self._log_debug("async_get_data", "Data read completed")
                if result:
                    self._mark_connection_healthy()
                    self._log_debug("async_get_data", "Data read successful")
                    return True
                self._mark_connection_unhealthy()
                self._log_debug("async_get_data", "Data read failed")
                return False
            self._log_debug("async_get_data", "Get Data failed: client not connected")
            return False
        except ConnectionException as connect_error:
            self._mark_connection_unhealthy()
            self._log_debug("async_get_data", f"Connection error: {connect_error}")
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            self._mark_connection_unhealthy()
            self._log_debug("async_get_data", f"Modbus error: {modbus_error}")
            raise ModbusError from modbus_error

    async def read_sunspec_modbus(self) -> bool:
        """Read Modbus Data Function."""
        try:
            # Only read device info if not cached or connection was unhealthy
            if self._should_read_device_info():
                await self.read_sunspec_modbus_model_1()
                self._device_info_cached = True

            # Always read live data (power, energy, etc.)
            await self.read_sunspec_modbus_model_101_103()
            # Find SunSpec Model 160 Offset and read data only if found
            if self.data["m160_offset"] == 0:
                # look for M160 offset only if not already found the first time
                self._log_debug(
                    "read_sunspec_modbus",
                    "M160 offset unknown, searching",
                    model=self.data["comm_model"],
                )
                if offset := await self.find_sunspec_modbus_m160_offset():
                    # M160 found, read and save offset in data dict for next cycle
                    await self.read_sunspec_modbus_model_160(offset)
                    self.data["m160_offset"] = offset
                    self._log_debug(
                        "read_sunspec_modbus",
                        "M160 found",
                        offset=self.data["m160_offset"],
                    )
                else:
                    # M160 not found, set offset to 1 so next cycle we skip the search
                    self.data["m160_offset"] = 1
                    self._log_debug(
                        "read_sunspec_modbus",
                        "M160 not found",
                        model=self.data["comm_model"],
                    )
            elif self.data["m160_offset"] == 1:
                # M160 offset has already been searched and wasn't found
                self._log_debug(
                    "read_sunspec_modbus",
                    "M160 not present",
                    model=self.data["comm_model"],
                )
            else:
                # M160 offset not 0/1, use the saved offset to read
                self._log_debug(
                    "read_sunspec_modbus",
                    "Using previously found M160",
                    model=self.data["comm_model"],
                    offset=self.data["m160_offset"],
                )
                await self.read_sunspec_modbus_model_160(self.data["m160_offset"])
            result = True
            self._log_debug("read_sunspec_modbus", "Completed", success=result)
        except ConnectionException as connect_error:
            result = False
            self._log_debug(
                "read_sunspec_modbus", "Completed with connection error", success=result
            )
            self._log_debug("read_sunspec_modbus", f"Connection error: {connect_error}")
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            result = False
            self._log_debug(
                "read_sunspec_modbus", "Completed with modbus error", success=result
            )
            self._log_debug("read_sunspec_modbus", f"Modbus error: {modbus_error}")
            raise ModbusError from modbus_error
        except Exception as exception_error:
            result = False
            self._log_debug(
                "read_sunspec_modbus", "Completed with generic error", success=result
            )
            self._log_debug("read_sunspec_modbus", f"Generic error: {exception_error}")
            raise ExceptionError from exception_error
        return result

    async def find_sunspec_modbus_m160_offset(self) -> int:
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
                self._log_debug(
                    "find_sunspec_modbus_m160_offset",
                    f"Searching M160 for model: {invmodel}",
                    offset=offset,
                )
                read_model_160_data = await self.read_holding_registers(
                    address=(self._base_addr + offset), count=1
                )
                if isinstance(read_model_160_data, ExceptionResponse):
                    # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
                    self._log_debug(
                        "find_sunspec_modbus_m160_offset",
                        f"Received Modbus exception: {read_model_160_data}",
                    )
                else:
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        read_model_160_data.registers,
                        byteorder=Endian.BIG,
                    )
                    multi_mppt_id = decoder.decode_16bit_uint()
                if multi_mppt_id != SUNSPEC_MODEL_160_ID:
                    self._log_debug(
                        "find_sunspec_modbus_m160_offset",
                        "Model is not 160",
                        offset=offset,
                        multi_mppt_id=multi_mppt_id,
                    )
                else:
                    self._log_debug(
                        "find_sunspec_modbus_m160_offset",
                        "Model is 160",
                        offset=offset,
                        multi_mppt_id=multi_mppt_id,
                    )
                    found_offset = offset
                    break
            if found_offset != 0:
                self._log_debug(
                    "find_sunspec_modbus_m160_offset",
                    f"Found M160 for model: {invmodel}",
                    offset=found_offset,
                )
            else:
                self._log_debug(
                    "find_sunspec_modbus_m160_offset",
                    f"M160 not found for model: {invmodel}",
                )
        except ConnectionException as connect_error:
            self._log_debug(
                "find_sunspec_modbus_m160_offset", f"Connection error: {connect_error}"
            )
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            self._log_debug(
                "find_sunspec_modbus_m160_offset", f"Modbus error: {modbus_error}"
            )
            raise ModbusError from modbus_error
        except Exception as exception_error:
            self._log_debug(
                "find_sunspec_modbus_m160_offset", f"Generic error: {exception_error}"
            )
            raise ExceptionError from exception_error
        return found_offset

    async def read_sunspec_modbus_model_1(self) -> bool:
        """Read SunSpec Model 1 Data."""
        # A single register is 2 bytes. Max number of registers in one read for Modbus/TCP is 123
        # https://control.com/forums/threads/maximum-amount-of-holding-registers-per-request.9904/post-86251
        #
        # So we have to do 2 read-cycles, one for M1 and the other for M103+M160
        #
        # Start address 4 read 64 registers to read M1 (Common Inverter Info) in 1-pass
        # Start address 72 read 92 registers to read (M101 or M103)+M160 (Realtime Power/Energy Data) in 1-pass
        try:
            self._log_debug(
                "read_sunspec_modbus_model_1",
                "Starting Model 1 read",
                slave_id=self._slave_id,
                base_addr=self._base_addr,
            )
            read_model_1_data = await self.read_holding_registers(
                address=(self._base_addr + 4), count=64
            )
            if isinstance(read_model_1_data, ExceptionResponse):
                # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
                self._log_debug(
                    "read_sunspec_modbus_model_1",
                    f"Received Modbus exception: {read_model_1_data}",
                )
                raise ModbusError
            # No connection errors, we can start scraping registers
            decoder = BinaryPayloadDecoder.fromRegisters(
                read_model_1_data.registers,
                byteorder=Endian.BIG,
            )
        except ConnectionException as connect_error:
            self._log_debug(
                "read_sunspec_modbus_model_1", f"Connection error: {connect_error}"
            )
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            self._log_debug(
                "read_sunspec_modbus_model_1", f"Modbus error: {modbus_error}"
            )
            raise ModbusError from modbus_error
        except Exception as exception_error:
            self._log_debug(
                "read_sunspec_modbus_model_1", f"Generic error: {exception_error}"
            )
            raise ExceptionError from exception_error

        # registers 4 to 43
        comm_manufact = decoder.decode_string(size=32).decode("ascii")
        comm_model = decoder.decode_string(size=32).decode("ascii")
        comm_options = decoder.decode_string(size=16).decode("ascii")
        self.data["comm_manufact"] = self._clean_string(comm_manufact)
        self.data["comm_model"] = self._clean_string(comm_model)
        self.data["comm_options"] = self._clean_string(comm_options)
        self._log_debug(
            "read_sunspec_modbus_model_1",
            "Device info read",
            manufacturer=self.data["comm_manufact"],
            model=self.data["comm_model"],
            options=self.data["comm_options"],
        )

        # Model based on options register, if unknown, raise an error to report it
        # First char is the model: if non-printable char, hex string of the char is provided
        # So we need to check if it's a char or an hex value string and convert both to a number
        # Then we lookup in the model table, if it's there, good, otherwise we provide the given model
        # test also with opt_model = '0x0DED/0xFFFF'
        opt_model = self.data["comm_options"]
        opt_model_int = self._parse_model_options(opt_model)
        if opt_model_int in DEVICE_MODEL:
            self.data["comm_model"] = DEVICE_MODEL[opt_model_int]
            self._log_debug(
                "read_sunspec_modbus_model_1",
                "Model from options",
                model=self.data["comm_model"],
            )
        else:
            self._log_error(
                "read_sunspec_modbus_model_1",
                "Model unknown, report to @alexdelprete on the forum the following data",
                manufacturer=self.data["comm_manufact"],
                model=self.data["comm_model"],
                options=self.data["comm_options"],
                opt_model=opt_model,
                opt_model_int=opt_model_int,
            )

        # registers 44 to 67
        comm_version = decoder.decode_string(size=16).decode("ascii")
        comm_sernum = decoder.decode_string(size=32).decode("ascii")
        self.data["comm_version"] = self._clean_string(comm_version)
        self.data["comm_sernum"] = self._clean_string(comm_sernum)
        self._log_debug(
            "read_sunspec_modbus_model_1",
            "Version read",
            version=self.data["comm_version"],
        )
        self._log_debug(
            "read_sunspec_modbus_model_1",
            "Serial number read",
            serial=self.data["comm_sernum"],
        )

        return True

    async def read_sunspec_modbus_model_101_103(self) -> bool:
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
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                "Starting Model 101/103 read",
                slave_id=self._slave_id,
                base_addr=self._base_addr,
            )
            read_model_101_103_data = await self.read_holding_registers(
                address=(self._base_addr + 70), count=40
            )
            if isinstance(read_model_101_103_data, ExceptionResponse):
                # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
                self._log_debug(
                    "read_sunspec_modbus_model_101_103",
                    f"Received Modbus exception: {read_model_101_103_data}",
                )
                raise ModbusError
            # No connection errors, we can start scraping registers
            decoder = BinaryPayloadDecoder.fromRegisters(
                read_model_101_103_data.registers,
                byteorder=Endian.BIG,
            )
        except ConnectionException as connect_error:
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                f"Connection error: {connect_error}",
            )
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            self._log_debug(
                "read_sunspec_modbus_model_101_103", f"Modbus error: {modbus_error}"
            )
            raise ModbusError from modbus_error
        except Exception as exception_error:
            self._log_debug(
                "read_sunspec_modbus_model_101_103", f"Generic error: {exception_error}"
            )
            raise ExceptionError from exception_error

        # register 70
        invtype = decoder.decode_16bit_uint()
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "Inverter type read",
            invtype_int=invtype,
            invtype_str=INVERTER_TYPE[invtype],
        )

        # make sure the value is in the known status list
        if invtype not in INVERTER_TYPE:
            invtype = 999
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                "Inverter type unknown",
                invtype_int=invtype,
                invtype_str=INVERTER_TYPE[invtype],
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
        self.data["accurrent"] = accurrent

        if invtype == 103:
            accurrenta = self.calculate_value(accurrenta, accurrentsf)
            accurrentb = self.calculate_value(accurrentb, accurrentsf)
            accurrentc = self.calculate_value(accurrentc, accurrentsf)
            self.data["accurrenta"] = accurrenta
            self.data["accurrentb"] = accurrentb
            self.data["accurrentc"] = accurrentc

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
        self.data["acvoltagean"] = acvoltagean

        if invtype == 103:
            acvoltageab = self.calculate_value(acvoltageab, acvoltagesf)
            acvoltagebc = self.calculate_value(acvoltagebc, acvoltagesf)
            acvoltageca = self.calculate_value(acvoltageca, acvoltagesf)
            acvoltagebn = self.calculate_value(acvoltagebn, acvoltagesf)
            acvoltagecn = self.calculate_value(acvoltagecn, acvoltagesf)
            self.data["acvoltageab"] = acvoltageab
            self.data["acvoltagebc"] = acvoltagebc
            self.data["acvoltageca"] = acvoltageca
            self.data["acvoltagebn"] = acvoltagebn
            self.data["acvoltagecn"] = acvoltagecn

        # registers 84 to 85
        acpower = decoder.decode_16bit_int()
        acpowersf = decoder.decode_16bit_int()
        acpower = self.calculate_value(acpower, acpowersf)
        self.data["acpower"] = acpower

        # registers 86 to 87
        acfreq = decoder.decode_16bit_uint()
        acfreqsf = decoder.decode_16bit_int()
        acfreq = self.calculate_value(acfreq, acfreqsf)
        self.data["acfreq"] = acfreq

        # skip register 88-93
        decoder.skip_bytes(12)

        # registers 94 to 96
        totalenergy = decoder.decode_32bit_uint()
        totalenergysf = decoder.decode_16bit_uint()
        totalenergy = self.calculate_value(totalenergy, totalenergysf)
        # ensure that totalenergy is always an increasing value (total_increasing)
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "Total energy read",
            total_energy=totalenergy,
            previous_energy=self.data["totalenergy"],
        )
        if totalenergy < self.data["totalenergy"]:
            self._log_error(
                "read_sunspec_modbus_model_101_103",
                "Total Energy less than previous value!",
                value_read=totalenergy,
                previous_value=self.data["totalenergy"],
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
            self.data["dccurr"] = dccurr
            self.data["dcvolt"] = dcvolt
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                "DC values read",
                dc_current=self.data["dccurr"],
                dc_voltage=self.data["dcvolt"],
            )
        else:
            decoder.skip_bytes(8)

        # registers 101 to 102
        dcpower = decoder.decode_16bit_int()
        dcpowersf = decoder.decode_16bit_int()
        dcpower = self.calculate_value(dcpower, dcpowersf)
        self.data["dcpower"] = dcpower
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "DC power read",
            dc_power=self.data["dcpower"],
        )
        # register 103
        tempcab = decoder.decode_16bit_int()
        # skip registers 104-105
        decoder.skip_bytes(4)
        # register 106 to 107
        tempoth = decoder.decode_16bit_int()
        tempsf = decoder.decode_16bit_int()
        # Fix for tempcab: in some inverters SF must be -2 not -1 as per specs
        tempcab = self._apply_temperature_correction(tempcab, tempsf)
        tempoth = self.calculate_value(tempoth, tempsf)
        self.data["tempoth"] = tempoth
        self.data["tempcab"] = tempcab
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "Temperature values read",
            temp_other=self.data["tempoth"],
            temp_cabinet=self.data["tempcab"],
        )
        # register 108
        status = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if status not in DEVICE_STATUS:
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                f"Unknown Operating State: {status}",
            )
            status = 999
        self.data["status"] = DEVICE_STATUS[status]
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "Device status read",
            status=self.data["status"],
        )

        # register 109
        statusvendor = decoder.decode_16bit_int()
        # make sure the value is in the known status list
        if statusvendor not in DEVICE_GLOBAL_STATUS:
            self._log_debug(
                "read_sunspec_modbus_model_101_103",
                "Unknown vendor operating state",
                statusvendor=statusvendor,
            )
            statusvendor = 999
        self.data["statusvendor"] = DEVICE_GLOBAL_STATUS[statusvendor]
        self._log_debug(
            "read_sunspec_modbus_model_101_103",
            "Status vendor read",
            statusvendor=self.data["statusvendor"],
        )
        self._log_debug("read_sunspec_modbus_model_101_103", "Completed")
        return True

    async def read_sunspec_modbus_model_160(self, offset: int = 122) -> bool:
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
            self._log_debug(
                "read_sunspec_modbus_model_160",
                "Starting Model 160 read",
                model=invmodel,
                slave_id=self._slave_id,
                base_addr=self._base_addr,
                offset=offset,
            )
            read_model_160_data = await self.read_holding_registers(
                address=(self._base_addr + offset), count=42
            )
            if isinstance(read_model_160_data, ExceptionResponse):
                # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
                self._log_debug(
                    "read_sunspec_modbus_model_160",
                    f"Received Modbus exception: {read_model_160_data}",
                )
                raise ModbusError
            # No connection errors, we can start scraping registers
            decoder = BinaryPayloadDecoder.fromRegisters(
                read_model_160_data.registers,
                byteorder=Endian.BIG,
            )
        except ConnectionException as connect_error:
            self._log_debug(
                "read_sunspec_modbus_model_160", f"Connection error: {connect_error}"
            )
            raise ConnectionError from connect_error
        except ModbusException as modbus_error:
            self._log_debug(
                "read_sunspec_modbus_model_160", f"Modbus error: {modbus_error}"
            )
            raise ModbusError from modbus_error
        except Exception as exception_error:
            self._log_debug(
                "read_sunspec_modbus_model_160", f"Generic error: {exception_error}"
            )
            raise ExceptionError from exception_error

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
        self._log_debug(
            "read_sunspec_modbus_model_160", "MPPT count read", mppt_count=multi_mppt_nr
        )

        # if we have at least one DC module
        if multi_mppt_nr >= 1:
            # skip register 131 to 140
            decoder.skip_bytes(20)

            # registers 141 to 143
            dc1curr = decoder.decode_16bit_uint()
            dc1volt = decoder.decode_16bit_uint()
            dc1power = decoder.decode_16bit_uint()
            dc1curr = self.calculate_value(dc1curr, dcasf)
            self.data["dc1curr"] = dc1curr
            dc1volt = self.calculate_value(dc1volt, dcvsf)
            self.data["dc1volt"] = dc1volt
            # this fixes dcvolt -0.0 for UNO-DM/REACT2 models
            self.data["dcvolt"] = dc1volt
            dc1power = self.calculate_value(dc1power, dcwsf)
            self.data["dc1power"] = dc1power
            self._log_debug(
                "read_sunspec_modbus_model_160",
                "DC1 values read",
                dc1_current=self.data["dc1curr"],
                dc1_voltage=self.data["dc1volt"],
                dc1_power=self.data["dc1power"],
                scale_factor=dcasf,
            )

        # if we have more than one DC module
        if multi_mppt_nr > 1:
            # skip register 144 to 160
            decoder.skip_bytes(34)

            # registers 161 to 163
            dc2curr = decoder.decode_16bit_uint()
            dc2volt = decoder.decode_16bit_uint()
            dc2power = decoder.decode_16bit_uint()
            dc2curr = self.calculate_value(dc2curr, dcasf)
            self.data["dc2curr"] = dc2curr
            dc2volt = self.calculate_value(dc2volt, dcvsf)
            self.data["dc2volt"] = dc2volt
            dc2power = self.calculate_value(dc2power, dcwsf)
            self.data["dc2power"] = dc2power
            self._log_debug(
                "read_sunspec_modbus_model_160",
                "DC2 values read",
                dc2_current=self.data["dc2curr"],
                dc2_voltage=self.data["dc2volt"],
                dc2_power=self.data["dc2power"],
                scale_factor=dcasf,
            )

        self._log_debug("read_sunspec_modbus_model_160", "Completed")
        return True
