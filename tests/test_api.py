"""SunSpec decoding tests for the API, against an in-memory Modbus unit."""

from __future__ import annotations

from unittest.mock import AsyncMock

from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusError,
    ModbusExceptionError,
    ModbusProtocolError,
)
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest

from custom_components.abb_powerone_pvi_sunspec.api import ABBPowerOneFimerAPI
from custom_components.abb_powerone_pvi_sunspec.const import (
    DEFAULT_CURRENT_VALUE,
    DEFAULT_VOLTAGE_VALUE,
)

from .registers import M103_START, InverterSpec, MpptSpec, build_register_map

M1_ADDRESS = 4


def make_api(
    spec: InverterSpec | None = None, base: int = 0
) -> tuple[ABBPowerOneFimerAPI, MockModbusUnit]:
    """Return an API reading a mock unit that serves ``spec`` at ``base``."""
    unit = MockModbusConnection().for_unit(2)
    unit.holding.update(build_register_map(spec, base=base))
    return ABBPowerOneFimerAPI("Inverter", "192.168.1.50", unit, base), unit


def read_addresses(unit: MockModbusUnit) -> list[int]:
    """Return the start address of every block read so far."""
    return [event.address for event in unit.read_events]


async def test_three_phase_dual_mppt() -> None:
    """Every data point of a three-phase, dual-MPPT inverter is decoded and scaled."""
    api, _ = make_api()

    data = await api.async_get_data()

    assert data is api.data
    assert data["comm_manufact"] == "Power-One"
    assert data["comm_model"] == "PVI-10.0-OUTD"  # from the options register
    assert data["comm_options"] == "X"
    assert data["comm_version"] == "C008"
    assert data["comm_sernum"] == "123456-3P75-1234"
    assert data["invtype"] == "Three Phase"
    assert data["accurrent"] == 12.34
    assert (data["accurrenta"], data["accurrentb"], data["accurrentc"]) == (4.11, 4.12, 4.13)
    assert (data["acvoltageab"], data["acvoltagebc"], data["acvoltageca"]) == (
        400.1,
        400.2,
        400.3,
    )
    assert (data["acvoltagean"], data["acvoltagebn"], data["acvoltagecn"]) == (
        230.1,
        230.2,
        230.3,
    )
    assert data["acpower"] == 4321
    assert data["acfreq"] == 50.02
    assert data["totalenergy"] == 12345678
    assert data["dcpower"] == 4450
    assert data["tempcab"] == 45.3
    assert data["tempoth"] == 41.2
    assert data["status"] == "MPPT"
    assert data["statusvendor"] == "Run"
    assert data["mppt_nr"] == 2
    assert (data["dc1curr"], data["dc1volt"], data["dc1power"]) == (3.21, 350.0, 800)
    assert (data["dc2curr"], data["dc2volt"], data["dc2power"]) == (2.5, 340.0, 750)
    # the DC voltage follows the first MPPT (the UNO-DM/REACT2 -0.0 fix)
    assert data["dcvolt"] == 350.0
    assert data["m160_offset"] == 122


async def test_single_phase_without_m160() -> None:
    """A single-phase inverter reads DC values from Model 101 and leaves phase values unset."""
    api, _ = make_api(InverterSpec(invtype=101, m160_offset=None))

    data = await api.async_get_data()

    assert data["invtype"] == "Single Phase"
    assert data["accurrent"] == 12.34
    assert data["acvoltagean"] == 230.1
    assert data["accurrenta"] == DEFAULT_CURRENT_VALUE
    assert data["acvoltageab"] == DEFAULT_VOLTAGE_VALUE
    assert data["dccurr"] == 5.12
    assert data["dcvolt"] == 345.6
    assert data["m160_offset"] == 1  # searched, not present


async def test_single_mppt() -> None:
    """With one DC module only the first MPPT is read."""
    api, _ = make_api(InverterSpec(mppts=[MpptSpec(100, 2000, 300)]))

    data = await api.async_get_data()

    assert data["mppt_nr"] == 1
    assert (data["dc1curr"], data["dc1volt"], data["dc1power"]) == (1.0, 200.0, 300)
    assert data["dc2power"] == 1  # untouched default


async def test_unknown_inverter_type() -> None:
    """An inverter type outside the table is reported as Unknown instead of failing."""
    api, _ = make_api(InverterSpec(invtype=102))

    data = await api.async_get_data()

    assert data["invtype"] == "Unknown"
    # treated as single phase for the per-phase registers
    assert data["accurrenta"] == DEFAULT_CURRENT_VALUE
    assert data["acvoltagean"] == 230.1


@pytest.mark.parametrize(
    ("status", "state"),
    [(1, "Off"), (2, "Sleeping"), (4, "MPPT"), (7, "Fault"), (8, "Standby"), (0xFFFF, "Unknown")],
)
async def test_operating_state_uses_sunspec_codes(status: int, state: str) -> None:
    """Register 108 is the SunSpec operating state, not ABB's Aurora inverter state."""
    api, _ = make_api(InverterSpec(status=status))

    data = await api.async_get_data()

    assert data["status"] == state


async def test_unknown_vendor_status() -> None:
    """A vendor status outside ABB's table maps to its 999 entry."""
    api, _ = make_api(InverterSpec(status_vendor=-5))

    data = await api.async_get_data()

    assert data["statusvendor"] == "Unknown"


async def test_cabinet_temperature_scale_factor_quirk() -> None:
    """A cabinet temperature above 70 °C is re-scaled with -2 instead of -1."""
    api, _ = make_api(InverterSpec(temp_cabinet=4530))

    data = await api.async_get_data()

    assert data["tempcab"] == 45.3


async def test_total_energy_never_decreases(caplog: pytest.LogCaptureFixture) -> None:
    """A lower total energy reading keeps the previous value and logs an error."""
    api, unit = make_api()
    await api.async_get_data()

    unit.holding.update(build_register_map(InverterSpec(energy_total=1000)))
    data = await api.async_get_data()

    assert data["totalenergy"] == 12345678
    assert "Total Energy less than previous value" in caplog.text


async def test_negative_energy_scale_factor() -> None:
    """The energy scale factor is signed, as SunSpec defines it."""
    api, _ = make_api(InverterSpec(energy_total=123456, energy_total_sf=-3))

    data = await api.async_get_data()

    assert data["totalenergy"] == 123.456


@pytest.mark.parametrize(
    ("options", "model"),
    [
        ("0x0D", "REACT2-UNO-5.0-TL"),  # non-printable model reported as hex
        (
            "0X0D/0xFFFF",
            "REACT2-UNO-5.0-TL",
        ),  # upper-case prefix, with the suffix some firmwares add
        ("0xZZ", "PVI-10.0-OUTD-raw"),  # not valid hex: model register kept
        ("X", "PVI-10.0-OUTD"),
        ("~", "PVI-10.0-OUTD-raw"),  # not in the table: model register kept
        ("", "PVI-10.0-OUTD-raw"),  # no options at all
    ],
)
async def test_model_from_options(options: str, model: str) -> None:
    """The model comes from the options register when the table knows it."""
    api, _ = make_api(InverterSpec(options=options))

    data = await api.async_get_data()

    assert data["comm_model"] == model


@pytest.mark.parametrize("offset", [1104, 208])
async def test_m160_found_at_alternate_offset(offset: int) -> None:
    """Model 160 is found after the default offset is refused or holds another model."""
    api, unit = make_api(InverterSpec(m160_offset=offset))
    unit.fail_read(122, IllegalDataAddressError())

    data = await api.async_get_data()

    assert data["m160_offset"] == offset
    assert data["mppt_nr"] == 2


async def test_m160_offset_is_remembered() -> None:
    """Later polls read Model 160 at the found offset without searching again."""
    api, unit = make_api(InverterSpec(m160_offset=1104))
    await api.async_get_data()
    unit.read_events.clear()

    await api.async_get_data()

    assert read_addresses(unit) == [M103_START, 1104]


async def test_missing_m160_is_not_searched_again() -> None:
    """Once Model 160 is known to be absent, later polls skip it."""
    api, unit = make_api(InverterSpec(m160_offset=None))
    await api.async_get_data()
    unit.read_events.clear()

    await api.async_get_data()

    assert read_addresses(unit) == [M103_START]


async def test_device_info_read_once_until_a_failure() -> None:
    """Model 1 is read on the first poll, skipped afterwards, and re-read after a failure."""
    api, unit = make_api()
    await api.async_get_data()
    assert M1_ADDRESS in read_addresses(unit)

    unit.read_events.clear()
    await api.async_get_data()
    assert M1_ADDRESS not in read_addresses(unit)

    unit.fail_requests(ModbusConnectionError("unplugged"))
    with pytest.raises(ModbusError):
        await api.async_get_data()
    unit.fail_requests(None)

    unit.read_events.clear()
    await api.async_get_data()
    assert read_addresses(unit)[0] == M1_ADDRESS


async def test_base_address_40000() -> None:
    """All models are read relative to the configured base address."""
    api, unit = make_api(base=40000)

    data = await api.async_get_data()

    assert data["comm_sernum"] == "123456-3P75-1234"
    assert data["m160_offset"] == 122
    assert read_addresses(unit) == [40004, 40070, 40122, 40122]


async def test_unreachable_inverter_raises() -> None:
    """A dead link surfaces as a ModbusError for the coordinator to handle."""
    api, unit = make_api()
    unit.fail_requests(ModbusConnectionError("no route to host"))

    with pytest.raises(ModbusConnectionError):
        await api.async_get_data()


async def test_refused_model_read_raises() -> None:
    """An exception response to a model read is not swallowed."""
    api, unit = make_api()
    unit.fail_read(M103_START, IllegalDataAddressError())

    with pytest.raises(ModbusExceptionError):
        await api.async_get_data()


async def test_properties_and_scaling() -> None:
    """The name and host are exposed, and scale factors round to their precision."""
    api, _ = make_api()

    assert api.name == "Inverter"
    assert api.host == "192.168.1.50"
    assert api.calculate_value(12345, -2) == 123.45
    assert api.calculate_value(12, 2) == 1200


async def test_not_implemented_values_have_no_reading() -> None:
    """SunSpec "not implemented" values become None instead of garbage readings."""
    api, _ = make_api(
        InverterSpec(
            ac_current=0xFFFF,  # uint16 not implemented
            ac_power=-0x8000,  # int16 not implemented
            ac_frequency_sf=-0x8000,  # scale factor not implemented
            temp_cabinet=-0x8000,
            mppts=[MpptSpec(0xFFFF, 3500, 800), MpptSpec(250, 3400, 750)],
        )
    )

    data = await api.async_get_data()

    assert data["accurrent"] is None
    assert data["accurrenta"] == 4.11  # its own value is implemented
    assert data["acpower"] is None
    assert data["acfreq"] is None
    assert data["tempcab"] is None
    assert data["tempoth"] == 41.2
    assert data["dc1curr"] is None
    assert data["dc1volt"] == 350.0


async def test_unavailable_total_energy_keeps_last_reading(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An energy counter reading 0 (SunSpec: not accumulated) keeps the last value silently."""
    api, unit = make_api()
    await api.async_get_data()

    unit.holding.update(build_register_map(InverterSpec(energy_total=0)))
    data = await api.async_get_data()

    assert data["totalenergy"] == 12345678
    assert "Total Energy less than previous value" not in caplog.text


async def test_not_implemented_mppt_count() -> None:
    """A Model 160 without a module count reads no DC inputs instead of failing."""
    api, unit = make_api()
    unit.holding[122 + 8] = 0x8000

    data = await api.async_get_data()

    assert data["mppt_nr"] == 0
    assert data["dc1power"] == 1  # untouched default


async def test_short_read_is_a_protocol_error() -> None:
    """A reply with fewer registers than requested is rejected, not decoded as zeros."""
    api, unit = make_api()
    unit.read_holding_registers = AsyncMock(return_value=[0] * 10)  # type: ignore[method-assign]

    with pytest.raises(ModbusProtocolError):
        await api.async_get_data()


async def test_unwrapped_transport_error_resets_device_info() -> None:
    """A raw OSError propagates and, like a Modbus error, forces Model 1 to be re-read."""
    api, unit = make_api()
    await api.async_get_data()

    unit.fail_requests(ConnectionResetError("reset by peer"))
    with pytest.raises(ConnectionResetError):
        await api.async_get_data()
    unit.fail_requests(None)

    unit.read_events.clear()
    await api.async_get_data()
    assert read_addresses(unit)[0] == M1_ADDRESS
