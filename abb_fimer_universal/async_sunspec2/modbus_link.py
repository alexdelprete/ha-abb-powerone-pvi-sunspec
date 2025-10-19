"""Abstract Modbus link used by the async SunSpec engine.

The engine depends on an abstract transport that can read Modbus holding
registers asynchronously. This allows swapping the concrete transport
implementation (e.g. pymodbus, bare TCP, serial gateways) and makes it easy to
mock for tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class ModbusLink(ABC):
    """Abstract asynchronous Modbus transport.

    Concrete implementations must be fully asynchronous and non-blocking.
    """

    unit_id: int

    def __init__(self, unit_id: int) -> None:
        self.unit_id = int(unit_id)

    @abstractmethod
    async def connect(self) -> None:
        """Establish the underlying transport connection if needed."""

    @abstractmethod
    async def close(self) -> None:
        """Close the transport and release resources."""

    @abstractmethod
    async def read_holding_registers(self, address: int, count: int) -> Sequence[int]:
        """Read a contiguous block of holding registers.

        Args:
            address: Zero-based Modbus register address (e.g., 40000 -> 0)
            count: Number of 16-bit registers to read

        Returns:
            A sequence of register values as Python ints in range 0..65535.
        """
        raise NotImplementedError
