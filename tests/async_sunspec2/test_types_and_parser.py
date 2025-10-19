"""Unit tests for async_sunspec2 types and parser."""

from __future__ import annotations

import math

from abb_fimer_universal.async_sunspec2.model_registry import (
    GroupDef,
    ModelDef,
    PointDef,
)
from abb_fimer_universal.async_sunspec2.parser import SunSpecParser
from abb_fimer_universal.async_sunspec2.types import INVALID_INT16, apply_scale


def _pack_string(s: str, size: int) -> list[int]:
    """Pack an ASCII string into SunSpec big-endian string registers."""
    s = (s or "").ljust(size, "\x00")[:size]
    bs = s.encode("ascii")
    regs = []
    for i in range(0, len(bs), 2):
        hi = bs[i]
        lo = bs[i + 1] if i + 1 < len(bs) else 0
        regs.append((hi << 8) | lo)
    return regs


def test_apply_scale_precision() -> None:
    """Validate scale application and precision handling."""
    assert apply_scale(100, -1) == 10.0
    assert apply_scale(1234, 0) == 1234
    assert math.isclose(apply_scale(1, -3), 0.001)


def test_parser_basic_types_and_sf() -> None:
    """Parse a small model exercising strings, sunssf and numeric points."""
    model = ModelDef(
        id=999,
        name="test",
        groups=[
            GroupDef(
                name="g",
                points=[
                    PointDef(name="Label", type="string", size=8, label="Label"),
                    PointDef(name="A_SF", type="sunssf"),
                    PointDef(name="A", type="int16", sfref="A_SF", units="A"),
                    PointDef(name="U", type="uint16", label="Unsigned"),
                    PointDef(name="I", type="int16", label="Signed"),
                ],
            )
        ],
    )

    regs: list[int] = []
    regs += _pack_string("ABCD", 8)  # 4 chars padded
    regs += [0xFFFF]  # A_SF = -1 -> represented as 0xFFFF in two's complement
    regs += [200]  # A = 200 -> 20.0 with sf -1
    regs += [0xFFFF]  # U invalid -> None
    regs += [INVALID_INT16]  # I invalid -> None

    res = SunSpecParser().parse(model, regs)
    assert res.model_id == 999
    assert res.points["Label"].raw == "ABCD"
    assert res.points["A_SF"].raw == -1
    assert res.points["A"].raw == 200
    assert math.isclose(res.points["A"].cvalue, 20.0)
    assert res.points["A"].precision == 1
    assert res.points["U"].raw is None
    assert res.points["I"].raw is None


def test_parser_repeating_group() -> None:
    """Parse a repeating group with N instances and validate scaling."""
    # Equivalent of a small subset of model 160: N followed by N triplets
    model = ModelDef(
        id=160,
        name="mppt_test",
        groups=[
            GroupDef(
                name="scales",
                points=[
                    PointDef(name="DCA_SF", type="sunssf"),
                    PointDef(name="DCV_SF", type="sunssf"),
                    PointDef(name="DCW_SF", type="sunssf"),
                    PointDef(name="N", type="uint16"),
                ],
            ),
            GroupDef(
                name="mppt",
                repeating=True,
                count_field="N",
                points=[
                    PointDef(name="DCA", type="uint16", sfref="DCA_SF"),
                    PointDef(name="DCV", type="uint16", sfref="DCV_SF"),
                    PointDef(name="DCW", type="uint16", sfref="DCW_SF"),
                ],
            ),
        ],
    )

    regs: list[int] = []
    # Scale factors: -1, 0, 0, N=2
    regs += [0xFFFF, 0, 0, 2]
    # MPPT 1: 123, 300, 350
    regs += [123, 300, 350]
    # MPPT 2: 456, 310, 360
    regs += [456, 310, 360]

    res = SunSpecParser().parse(model, regs)
    # Expect keys without suffix as we kept names the same; last write wins
    assert res.points["DCA"].raw == 456
    assert math.isclose(res.points["DCA"].cvalue, 45.6)
    assert res.points["DCV"].raw == 310
    assert res.points["DCW"].raw == 360
