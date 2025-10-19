"""Typed exception hierarchy used by the async_sunspec2 engine."""

from __future__ import annotations


class AsyncSunSpecError(Exception):
    """Base exception for async SunSpec engine errors."""


class TransportError(AsyncSunSpecError):
    """Transport/connection level error from the Modbus link."""


class ProtocolError(AsyncSunSpecError):
    """Modbus/SunSpec protocol violation or unexpected response."""


class ModelNotFoundError(AsyncSunSpecError):
    """Raised when a requested model definition is not available."""


class ScanError(AsyncSunSpecError):
    """Raised when scanning for the SunSpec map fails."""
