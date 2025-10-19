"""Async SunSpec v2 internal engine using ModbusLink and JSON model definitions.

This package provides an asynchronous SunSpec parsing and transport layer that
can be extracted into a standalone library. It discovers SunSpec models,
reads raw Modbus register blocks over an abstract ModbusLink, and parses
values using vendored SunSpec JSON model definitions.

Key modules:
- exceptions: typed exception hierarchy for transport/protocol/parser errors
- modbus_link: abstract transport interface for reading holding registers
- model_registry: loader and index for JSON model definitions
- parser: SunSpec base-type decoder and group/scale-factor aware parser
- scanner: Async client that discovers models and reads model blocks

The public API is intentionally small:
- AsyncSunSpecClient: async connect/close, scan(), read_model(), read_all()

All I/O is asynchronous and does not use thread executors.
"""

from .exceptions import (
    AsyncSunSpecError,
    TransportError,
    ProtocolError,
    ModelNotFoundError,
    ScanError,
)
from .modbus_link import ModbusLink
from .model_registry import ModelRegistry
from .parser import SunSpecParser, PointValue, ModelParseResult
from .scanner import AsyncSunSpecClient, ScanResult, DiscoveredModel

__all__ = [
    "AsyncSunSpecClient",
    "ScanResult",
    "DiscoveredModel",
    "ModbusLink",
    "ModelRegistry",
    "SunSpecParser",
    "PointValue",
    "ModelParseResult",
    "AsyncSunSpecError",
    "TransportError",
    "ProtocolError",
    "ModelNotFoundError",
    "ScanError",
]
