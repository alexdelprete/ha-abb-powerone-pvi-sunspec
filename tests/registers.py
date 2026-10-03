"""Build the SunSpec holding-register map of a test inverter.

The map is loaded into a ``modbus_connection.mock.MockModbusUnit``, so the real
API decodes the same register layout an inverter serves: Model 1 at
base + 4, Model 101/103 at base + 70 and, optionally, Model 160 at one of the
offsets the API searches.

Every reading is a raw register value plus a scale factor, as on the wire.
"""

from __future__ import annotations

from dataclasses import dataclass, field

M1_START = 4
M103_START = 70
M160_DEFAULT_OFFSET = 122
M160_ID = 160
M160_LENGTH = 40


@dataclass
class MpptSpec:
    """One DC input of Model 160: raw current, voltage and power."""

    current: int
    voltage: int
    power: int


@dataclass
class InverterSpec:
    """Register contents of a test inverter (defaults: three-phase, two MPPTs)."""

    manufacturer: str = "Power-One"
    model: str = "PVI-10.0-OUTD-raw"
    options: str = "X"  # ord("X") == 88 -> PVI-10.0-OUTD
    version: str = "C008"
    serial: str = "123456-3P75-1234"

    invtype: int = 103
    ac_current: int = 1234
    ac_current_abc: tuple[int, int, int] = (411, 412, 413)
    ac_current_sf: int = -2
    ac_voltage_ab_bc_ca: tuple[int, int, int] = (4001, 4002, 4003)
    ac_voltage_an: int = 2301
    ac_voltage_bn_cn: tuple[int, int] = (2302, 2303)
    ac_voltage_sf: int = -1
    ac_power: int = 4321
    ac_power_sf: int = 0
    ac_frequency: int = 5002
    ac_frequency_sf: int = -2
    energy_total: int = 12345678
    energy_total_sf: int = 0
    dc_current: int = 512
    dc_current_sf: int = -2
    dc_voltage: int = 3456
    dc_voltage_sf: int = -1
    dc_power: int = 4450
    dc_power_sf: int = 0
    temp_cabinet: int = 453
    temp_other: int = 412
    temp_sf: int = -1
    status: int = 4  # SunSpec MPPT: producing
    status_vendor: int = 6  # Run

    m160_offset: int | None = M160_DEFAULT_OFFSET
    """Where Model 160 starts; None for an inverter without it."""
    mppt_current_sf: int = -2
    mppt_voltage_sf: int = -1
    mppt_power_sf: int = 0
    mppts: list[MpptSpec] = field(
        default_factory=lambda: [MpptSpec(321, 3500, 800), MpptSpec(250, 3400, 750)]
    )


def words(value: int) -> int:
    """Return a signed or unsigned 16-bit value as its register word."""
    return value & 0xFFFF


def string_words(text: str, count: int) -> list[int]:
    """Encode ``text`` as ``count`` registers, two ASCII characters each, null padded."""
    raw = text.encode("ascii").ljust(count * 2, b"\x00")[: count * 2]
    return [int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw), 2)]


def build_register_map(spec: InverterSpec | None = None, base: int = 0) -> dict[int, int]:
    """Return ``{address: word}`` for every register the API reads from ``spec``."""
    spec = spec or InverterSpec()
    regs: dict[int, int] = {}

    def put(address: int, values: list[int]) -> None:
        for i, value in enumerate(values):
            regs[base + address + i] = words(value)

    # Model 1, registers 4 to 67
    put(M1_START, string_words(spec.manufacturer, 16))
    put(M1_START + 16, string_words(spec.model, 16))
    put(M1_START + 32, string_words(spec.options, 8))
    put(M1_START + 40, string_words(spec.version, 8))
    put(M1_START + 48, string_words(spec.serial, 16))

    # Model 101/103, registers 70 to 109
    put(
        M103_START,
        [
            spec.invtype,
            50,  # model length
            spec.ac_current,
            *spec.ac_current_abc,
            spec.ac_current_sf,
            *spec.ac_voltage_ab_bc_ca,
            spec.ac_voltage_an,
            *spec.ac_voltage_bn_cn,
            spec.ac_voltage_sf,
            spec.ac_power,
            spec.ac_power_sf,
            spec.ac_frequency,
            spec.ac_frequency_sf,
            0,  # VA
            0,  # VA_SF
            0,  # VAr
            0,  # VAr_SF
            0,  # PF
            0,  # PF_SF
            spec.energy_total >> 16,
            spec.energy_total & 0xFFFF,
            spec.energy_total_sf,
            spec.dc_current,
            spec.dc_current_sf,
            spec.dc_voltage,
            spec.dc_voltage_sf,
            spec.dc_power,
            spec.dc_power_sf,
            spec.temp_cabinet,
            0,  # TmpSnk
            0,  # TmpTrns
            spec.temp_other,
            spec.temp_sf,
            spec.status,
            spec.status_vendor,
        ],
    )

    # Model 160, 42 registers from its offset
    if spec.m160_offset is not None:
        block = [0] * 42
        block[0] = M160_ID
        block[1] = M160_LENGTH
        block[2] = spec.mppt_current_sf
        block[3] = spec.mppt_voltage_sf
        block[4] = spec.mppt_power_sf
        block[8] = len(spec.mppts)
        # each module is 20 registers from register 10; current, voltage, power at +9..+11
        for index, mppt in enumerate(spec.mppts[:2]):
            start = 10 + 20 * index
            block[start] = index + 1
            block[start + 9 : start + 12] = [mppt.current, mppt.voltage, mppt.power]
        put(spec.m160_offset, block)

    return regs
