"""Async SunSpec client that uses a ModbusLink for discovery and reading."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .exceptions import ModelNotFoundError, ProtocolError, ScanError, TransportError
from .modbus_link import ModbusLink
from .model_registry import ModelRegistry
from .parser import ModelParseResult, SunSpecParser


SUNS_SIGNATURE = b"SunS"
MAX_REGS_PER_READ = 125


@dataclass(slots=True)
class DiscoveredModel:
    """Model discovered during a scan."""

    model_id: int
    length: int
    data_address: int  # absolute register address where model data begins


@dataclass(slots=True)
class ScanResult:
    """Result of a SunSpec scan: base address and model layout."""

    base_address: int
    models: list[DiscoveredModel]


class AsyncSunSpecClient:
    """Async client using a ModbusLink to discover and parse SunSpec models."""

    def __init__(
        self, link: ModbusLink, *, base_candidates: Iterable[int] | None = None
    ) -> None:
        """Create a new async SunSpec client.

        Args:
            link: Modbus transport/link to use for register reads
            base_candidates: Optional list of candidate SunSpec base addresses
        """
        self._link = link
        self._parser = SunSpecParser()
        self._registry = ModelRegistry()
        self._registry.load()
        self._base_candidates = list(base_candidates or (0, 40000, 50000))
        self._scan: ScanResult | None = None

    async def connect(self) -> None:
        """Establish the underlying transport connection."""
        try:
            await self._link.connect()
        except Exception as exc:
            raise TransportError("failed to connect transport") from exc

    async def close(self) -> None:
        """Close the underlying transport connection."""
        try:
            await self._link.close()
        except Exception as exc:
            raise TransportError("failed to close transport") from exc

    async def _read(self, address: int, count: int) -> list[int]:
        """Read a register block, splitting into Modbus-safe chunks."""
        regs: list[int] = []
        remaining = count
        offset = 0
        while remaining > 0:
            chunk = min(remaining, MAX_REGS_PER_READ)
            try:
                part = list(
                    await self._link.read_holding_registers(address + offset, chunk)
                )
            except Exception as exc:
                raise TransportError("modbus read failed") from exc
            if len(part) != chunk:
                raise ProtocolError("short read from transport")
            regs.extend(part)
            remaining -= chunk
            offset += chunk
        return regs

    @staticmethod
    def _decode_string_from_regs(regs: list[int]) -> str:
        bs = bytearray()
        for w in regs:
            bs.append((w >> 8) & 0xFF)
            bs.append(w & 0xFF)
        return bs.decode("ascii", errors="ignore")

    async def scan(self) -> ScanResult:
        """Discover the SunSpec base and enumerate models."""
        # Find SunS marker at common base candidates
        base_addr = None
        for cand in self._base_candidates:
            try:
                regs = await self._read(cand, 2)
            except TransportError:
                continue
            if self._decode_string_from_regs(regs)[:4] == SUNS_SIGNATURE.decode():
                base_addr = cand
                break
        if base_addr is None:
            raise ScanError("SunSpec signature not found at candidates")

        # Walk models
        models: list[DiscoveredModel] = []
        ptr = base_addr + 2
        while True:
            hdr = await self._read(ptr, 2)
            model_id = hdr[0] & 0xFFFF
            length = hdr[1] & 0xFFFF
            if model_id == 0xFFFF:
                break
            models.append(
                DiscoveredModel(model_id=model_id, length=length, data_address=ptr + 2)
            )
            ptr += 2 + length

        self._scan = ScanResult(base_address=base_addr, models=models)
        return self._scan

    def _ensure_scan(self) -> ScanResult:
        if self._scan is None:
            raise ScanError("scan() not called yet")
        return self._scan

    async def read_model(self, model_id: int) -> ModelParseResult:
        """Read and parse a specific model by its id."""
        scan = self._ensure_scan()
        matches = [m for m in scan.models if m.model_id == model_id]
        if not matches:
            raise ModelNotFoundError(f"model {model_id} not present in scan")
        m = matches[0]
        regs = await self._read(m.data_address, m.length)
        # Parse using registry definition
        model_def = self._registry.get_by_id(model_id)
        return self._parser.parse(model_def, regs)

    async def read_all(self) -> dict[int, ModelParseResult]:
        """Read and parse all discovered models that have JSON definitions."""
        scan = self._ensure_scan()
        out: dict[int, ModelParseResult] = {}
        for m in scan.models:
            try:
                model_def = self._registry.get_by_id(m.model_id)
            except KeyError:
                # Unknown model JSON not present; skip silently
                continue
            regs = await self._read(m.data_address, m.length)
            out[m.model_id] = self._parser.parse(model_def, regs)
        return out
