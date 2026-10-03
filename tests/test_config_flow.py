"""Config and options flow tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

from modbus_connection import ModbusConnectionError, ModbusTimeoutError
from modbus_connection.mock import MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError

from .conftest import TEST_SERIAL, USER_INPUT
from .registers import InverterSpec, build_register_map

TEMPORARY_UNIT = "custom_components.abb_powerone_pvi_sunspec.config_flow.async_get_temporary_unit"


async def start_user_flow(hass: HomeAssistant, **overrides: Any) -> dict[str, Any]:
    """Submit the user step with USER_INPUT and ``overrides``."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**USER_INPUT, **overrides}
    )


def raising_unit(error: Exception) -> Any:
    """Return an async_get_temporary_unit replacement that raises ``error`` on entry."""

    @asynccontextmanager
    async def temporary_unit(*args: Any, **kwargs: Any) -> AsyncIterator[MockModbusUnit]:
        raise error
        yield  # pragma: no cover

    return temporary_unit


async def test_user_form_is_shown(hass: HomeAssistant) -> None:
    """The user step starts with an empty form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """A reachable inverter creates an entry keyed by its serial number."""
    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT["name"]
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == TEST_SERIAL


@pytest.mark.parametrize(
    "error",
    [
        ModbusConnectionError("no route to host"),
        ModbusTimeoutError("timed out"),
        ConnectionResetError("reset by peer"),
    ],
)
async def test_user_flow_cannot_connect(
    hass: HomeAssistant, mock_unit: MockModbusUnit, error: Exception
) -> None:
    """Any failure to read the inverter keeps the form open with cannot_connect."""
    mock_unit.fail_requests(error)

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_recovers_after_error(
    hass: HomeAssistant, mock_unit: MockModbusUnit
) -> None:
    """After a failed attempt the form keeps the input, and a retry can succeed."""
    mock_unit.fail_requests(ModbusConnectionError("no route to host"))
    result = await start_user_flow(hass, host="192.168.1.77")
    assert result["errors"] == {"base": "cannot_connect"}

    mock_unit.fail_requests(None)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_HOST: "192.168.1.77"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == "192.168.1.77"


async def test_user_flow_inverter_without_serial(
    hass: HomeAssistant, mock_unit: MockModbusUnit
) -> None:
    """An inverter reporting no serial number cannot be added: there is nothing to key it by."""
    mock_unit.holding.update(build_register_map(InverterSpec(serial="")))

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_serial_number"}


async def test_user_flow_modbus_link_conflict(hass: HomeAssistant) -> None:
    """A device held by another integration with other link settings is reported, not added."""
    with patch(TEMPORARY_UNIT, raising_unit(HomeAssistantError("already in use"))):
        result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "modbus_link_conflict"}


async def test_user_flow_unexpected_error(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected exception is logged with its traceback and reported as unknown."""
    with patch(TEMPORARY_UNIT, raising_unit(RuntimeError("boom"))):
        result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}
    assert "Unexpected error reading the inverter" in caplog.text


async def test_user_flow_invalid_host(hass: HomeAssistant) -> None:
    """A malformed host is rejected before any connection attempt."""
    result = await start_user_flow(hass, host="not a host!")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOST: "invalid_host"}


async def test_user_flow_host_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The same host cannot be added twice."""
    config_entry.add_to_hass(hass)

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOST: "already_configured"}


async def test_user_flow_same_inverter_on_another_host(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The same serial number behind a different host aborts as already configured."""
    config_entry.add_to_hass(hass)

    result = await start_user_flow(hass, host="192.168.1.51")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


def options_input(**overrides: Any) -> dict[str, Any]:
    """Return the options form input for the test entry with ``overrides``."""
    return {
        CONF_HOST: USER_INPUT[CONF_HOST],
        CONF_PORT: USER_INPUT[CONF_PORT],
        CONF_DEVICE_ID: USER_INPUT[CONF_DEVICE_ID],
        CONF_BASE_ADDR: USER_INPUT[CONF_BASE_ADDR],
        CONF_SCAN_INTERVAL: USER_INPUT[CONF_SCAN_INTERVAL],
        **overrides,
    }


async def submit_options(
    hass: HomeAssistant, entry: MockConfigEntry, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Open the options flow of ``entry`` and submit ``user_input``."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    return await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=user_input
    )


async def test_options_flow_updates_entry_and_reloads(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """New connection settings that reach the same inverter are saved and the entry reloads.

    Regression test: the update listener used to be a plain function, which
    HA 2026.9 schedules as a task, so saving options handed it None.
    """
    result = await submit_options(
        hass, init_integration, options_input(port=1502, device_id=3.0, scan_interval=120)
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert init_integration.data[CONF_PORT] == 1502
    assert init_integration.data[CONF_SCAN_INTERVAL] == 120
    assert init_integration.data["name"] == USER_INPUT["name"]
    assert init_integration.state is ConfigEntryState.LOADED


async def test_options_flow_scan_interval_only_skips_connection_test(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """Changing only the polling interval works while the inverter is unreachable."""
    mock_unit.fail_requests(ModbusConnectionError("inverter asleep"))

    # the unit id comes back from the number selector as a float
    result = await submit_options(
        hass, init_integration, options_input(device_id=2.0, scan_interval=300)
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert init_integration.data[CONF_SCAN_INTERVAL] == 300


@pytest.mark.parametrize(
    ("overrides", "errors"),
    [
        ({CONF_HOST: "not a host!"}, {CONF_HOST: "invalid_host"}),
        ({CONF_PORT: 1502}, {"base": "cannot_connect"}),
    ],
)
async def test_options_flow_rejects_unusable_settings(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_unit: MockModbusUnit,
    overrides: dict[str, Any],
    errors: dict[str, str],
) -> None:
    """New connection settings are tested and refused if the inverter cannot be read."""
    mock_unit.fail_requests(ModbusConnectionError("connection refused"))

    result = await submit_options(hass, init_integration, options_input(**overrides))

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == errors
    assert init_integration.data == USER_INPUT


async def test_options_flow_rejects_a_different_inverter(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """Settings that reach another inverter would orphan this entry's entities: refused."""
    mock_unit.holding.update(build_register_map(InverterSpec(serial="999999-0000-0000")))

    result = await submit_options(hass, init_integration, options_input(host="192.168.1.99"))

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "wrong_device"}
    assert init_integration.data[CONF_HOST] == USER_INPUT[CONF_HOST]


async def test_options_flow_defaults_from_v1_slave_id(hass: HomeAssistant) -> None:
    """An entry still carrying slave_id offers it as the device id default."""
    data = {k: v for k, v in USER_INPUT.items() if k != "device_id"} | {"slave_id": 7}
    entry = MockConfigEntry(domain=DOMAIN, data=data, unique_id=TEST_SERIAL, version=2)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    schema = result["data_schema"].schema
    device_id_key = next(key for key in schema if key == "device_id")
    assert device_id_key.default() == 7
