"""SunSpec base-type decoding helpers and constants."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

# SunSpec invalid sentinels
INVALID_INT16: Final[int] = 0x8000
INVALID_UINT16: Final[int] = 0xFFFF
INVALID_INT32: Final[int] = 0x8000_0000
INVALID_UINT32: Final[int] = 0xFFFF_FFFF
INVALID_INT64: Final[int] = 0x8000_0000_0000_0000
INVALID_UINT64: Final[int] = 0xFFFF_FFFF_FFFF_FFFF


@dataclass(slots=True)
class DecodeResult:
    """A value decoded from registers."""

    value: int | float | str | None
    regs_used: int


def _to_signed(v: int, bits: int) -> int:
    mask = (1 << bits) - 1
    v = v & mask
    sign_bit = 1 << (bits - 1)
    return v - (1 << bits) if (v & sign_bit) else v


def decode_int16(regs: Sequence[int]) -> DecodeResult:
    """Decode a signed 16-bit integer with SunSpec invalid sentinel handling."""
    v = _to_signed(regs[0], 16)
    if v == _to_signed(INVALID_INT16, 16):
        return DecodeResult(None, 1)
    return DecodeResult(v, 1)


def decode_uint16(regs: Sequence[int]) -> DecodeResult:
    """Decode an unsigned 16-bit integer with SunSpec invalid sentinel handling."""
    v = regs[0] & 0xFFFF
    if v == INVALID_UINT16:
        return DecodeResult(None, 1)
    return DecodeResult(v, 1)


def decode_enum16(regs: Sequence[int]) -> DecodeResult:
    """Decode a 16-bit enum (same handling as uint16)."""
    return decode_uint16(regs)


def decode_bitfield16(regs: Sequence[int]) -> DecodeResult:
    """Decode a 16-bit bitfield (same handling as uint16)."""
    return decode_uint16(regs)


def decode_int32(regs: Sequence[int]) -> DecodeResult:
    """Decode a signed 32-bit integer from two registers."""
    raw = ((regs[0] & 0xFFFF) << 16) | (regs[1] & 0xFFFF)
    v = _to_signed(raw, 32)
    if v == _to_signed(INVALID_INT32, 32):
        return DecodeResult(None, 2)
    return DecodeResult(v, 2)


def decode_uint32(regs: Sequence[int]) -> DecodeResult:
    """Decode an unsigned 32-bit integer from two registers."""
    v = ((regs[0] & 0xFFFF) << 16) | (regs[1] & 0xFFFF)
    if v == INVALID_UINT32:
        return DecodeResult(None, 2)
    return DecodeResult(v, 2)


def decode_acc32(regs: Sequence[int]) -> DecodeResult:
    """Decode a 32-bit accumulator (same handling as uint32)."""
    return decode_uint32(regs)


def decode_int64(regs: Sequence[int]) -> DecodeResult:
    """Decode a signed 64-bit integer from four registers."""
    raw = (
        ((regs[0] & 0xFFFF) << 48)
        | ((regs[1] & 0xFFFF) << 32)
        | ((regs[2] & 0xFFFF) << 16)
        | (regs[3] & 0xFFFF)
    )
    v = _to_signed(raw, 64)
    if v == _to_signed(INVALID_INT64, 64):
        return DecodeResult(None, 4)
    return DecodeResult(v, 4)


def decode_uint64(regs: Sequence[int]) -> DecodeResult:
    """Decode an unsigned 64-bit integer from four registers."""
    v = (
        ((regs[0] & 0xFFFF) << 48)
        | ((regs[1] & 0xFFFF) << 32)
        | ((regs[2] & 0xFFFF) << 16)
        | (regs[3] & 0xFFFF)
    )
    if v == INVALID_UINT64:
        return DecodeResult(None, 4)
    return DecodeResult(v, 4)


def decode_acc64(regs: Sequence[int]) -> DecodeResult:
    """Decode a 64-bit accumulator (same handling as uint64)."""
    return decode_uint64(regs)


def decode_sunssf(regs: Sequence[int]) -> DecodeResult:
    """Decode a sunssf exponent (signed 16-bit)."""
    return decode_int16(regs)


def decode_string(regs: Sequence[int], size_bytes: int) -> DecodeResult:
    """Decode a fixed-size SunSpec string packed as big-endian bytes per word."""
    n_regs = (size_bytes + 1) // 2
    bs = bytearray()
    for i in range(n_regs):
        word = regs[i] & 0xFFFF
        bs.append((word >> 8) & 0xFF)
        bs.append(word & 0xFF)
    s = bs[:size_bytes].decode("ascii", errors="ignore").rstrip("\x00\x20")
    # If the string is empty, return empty string rather than None
    return DecodeResult(s, n_regs)


# Simple dispatch map for fixed-size types
DECODERS = {
    "int16": decode_int16,
    "uint16": decode_uint16,
    "enum16": decode_enum16,
    "bitfield16": decode_bitfield16,
    "int32": decode_int32,
    "uint32": decode_uint32,
    "acc32": decode_acc32,
    "int64": decode_int64,
    "uint64": decode_uint64,
    "acc64": decode_acc64,
    "sunssf": decode_sunssf,
}


def decode_value(
    typ: str, regs: Sequence[int], *, size_bytes: int | None = None
) -> DecodeResult:
    """Decode a SunSpec value of the given type from the register stream.

    For strings, provide size_bytes; for fixed-size types, size is ignored.
    """
    if typ == "string":
        if size_bytes is None:
            raise ValueError("size_bytes required for string type")
        return decode_string(regs, size_bytes)
    if typ not in DECODERS:
        raise ValueError(f"Unsupported SunSpec type: {typ}")
    return DECODERS[typ](regs)


def apply_scale(raw: float | None, sf: int | None) -> float | None:
    """Apply sunssf scaling to a raw value, returning a cvalue.

    SunSpec defines scale factor as base-10 exponent to apply to the raw integer
    to obtain engineering value.
    """
    if raw is None:
        return None
    if sf is None:
        return raw
    # Use pow to preserve precision for negative exponents
    return float(raw) * (10.0 ** float(sf))


def precision_from_sf(sf: int | None) -> int | None:
    """Return the decimal precision implied by the scale factor (non-negative)."""
    if sf is None:
        return None
    return int(abs(min(sf, 0)))
