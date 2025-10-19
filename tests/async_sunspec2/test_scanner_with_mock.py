"""Integration-style test for the async scanner using a mocked ModbusLink."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from abb_fimer_universal.async_sunspec2 import AsyncSunSpecClient
from abb_fimer_universal.async_sunspec2.modbus_link import ModbusLink


@dataclass
class _MockLink(ModbusLink):
    """Simple memory-backed Modbus link for tests."""

    mem: dict[int, int]

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def read_holding_registers(self, address: int, count: int) -> Sequence[int]:
        return [self.mem.get(a, 0) for a in range(address, address + count)]


def _pack_string_regs(s: str) -> list[int]:
    """Pack an ASCII string as SunSpec string registers."""
    bs = s.encode("ascii")
    # Ensure even length
    if len(bs) % 2:
        bs += b"\x00"
    return [(bs[i] << 8) | bs[i + 1] for i in range(0, len(bs), 2)]


def test_scan_and_parse_model_1() -> None:
    """Scan a simple map and parse Model 1 using bundled JSON."""
    # Build a simple SunSpec map: SunS, M1 header+data, end
    base = 40000
    mem: dict[int, int] = {}
    # SunS signature
    sig = _pack_string_regs("SunS")
    mem[base] = sig[0]
    mem[base + 1] = sig[1]

    # Model 1 header: id=1, len=64
    mem[base + 2] = 1
    mem[base + 3] = 64

    # Model 1 data (5 strings): 32+32+16+16+32 bytes -> 64 regs
    data_regs = []
    data_regs += _pack_string_regs("ABB") + [0] * (16 - len(_pack_string_regs("ABB")))
    data_regs += _pack_string_regs("UNO") + [0] * (16 - len(_pack_string_regs("UNO")))
    data_regs += _pack_string_regs("OPT") + [0] * (8 - len(_pack_string_regs("OPT")))
    data_regs += _pack_string_regs("1.0.0") + [0] * (
        8 - len(_pack_string_regs("1.0.0"))
    )
    data_regs += _pack_string_regs("12345678") + [0] * (
        16 - len(_pack_string_regs("12345678"))
    )
    assert len(data_regs) == 64

    for i, w in enumerate(data_regs):
        mem[base + 4 + i] = w

    # End marker
    mem[base + 4 + 64] = 0xFFFF
    mem[base + 4 + 65] = 0

    link = _MockLink(unit_id=2, mem=mem)
    client = AsyncSunSpecClient(link)

    # Scan and read
    async def run() -> None:
        await client.connect()
        await client.scan()
        m1 = await client.read_model(1)
        await client.close()
        assert m1.model_id == 1
        assert m1.points["Mn"].raw == "ABB"
        assert m1.points["Md"].raw == "UNO"
        assert m1.points["SN"].raw == "12345678"

    asyncio.get_event_loop().run_until_complete(run())
