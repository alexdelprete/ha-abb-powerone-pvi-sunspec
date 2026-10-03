"""Config and options flow tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

from modbus_connection import ModbusConnectionError
from modbus_connection.mock import MockModbusUnit
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.const import (
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


async def start_user_flow(hass: HomeAssistant, **overrides: Any) -> dict[str, Any]:
    """Submit the user step with USER_INPUT and ``overrides``."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**USER_INPUT, **overrides}
    )


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


async def test_user_flow_unreachable_inverter(
    hass: HomeAssistant, mock_unit: MockModbusUnit
) -> None:
    """An unreachable inverter keeps the form open with a host error."""
    mock_unit.fail_requests(ModbusConnectionError("no route to host"))

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_inverter_without_serial(
    hass: HomeAssistant, mock_unit: MockModbusUnit
) -> None:
    """An inverter reporting no serial number cannot be added: there is nothing to key it by."""
    mock_unit.holding.update(build_register_map(InverterSpec(serial="")))

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_modbus_link_conflict(hass: HomeAssistant) -> None:
    """A device held by another integration with other link settings is reported, not added."""

    @asynccontextmanager
    async def conflicting_unit(*args: Any, **kwargs: Any) -> AsyncIterator[MockModbusUnit]:
        raise HomeAssistantError("already in use")
        yield  # pragma: no cover

    with patch(
        "custom_components.abb_powerone_pvi_sunspec.config_flow.async_get_temporary_unit",
        conflicting_unit,
    ):
        result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_invalid_host(hass: HomeAssistant) -> None:
    """A malformed host is rejected before any connection attempt."""
    result = await start_user_flow(hass, host="not a host!")

    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_host_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The same host cannot be added twice."""
    config_entry.add_to_hass(hass)

    result = await start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_same_inverter_on_another_host(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The same serial number behind a different host aborts as already configured."""
    config_entry.add_to_hass(hass)

    result = await start_user_flow(hass, host="192.168.1.51")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_updates_entry_and_reloads(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Saving options rewrites the entry data and reloads it cleanly.

    Regression test: the update listener used to be a plain function, which
    HA 2026.9 schedules as a task, so saving options handed it None.
    """
    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    new_options = {
        CONF_HOST: USER_INPUT[CONF_HOST],
        CONF_PORT: 1502,
        "device_id": 3,
        "base_addr": 0,
        CONF_SCAN_INTERVAL: 120,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=new_options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert init_integration.data[CONF_PORT] == 1502
    assert init_integration.data[CONF_SCAN_INTERVAL] == 120
    assert init_integration.data["name"] == USER_INPUT["name"]
    assert init_integration.state is ConfigEntryState.LOADED


async def test_options_flow_defaults_from_v1_slave_id(hass: HomeAssistant) -> None:
    """An entry still carrying slave_id offers it as the device id default."""
    data = {k: v for k, v in USER_INPUT.items() if k != "device_id"} | {"slave_id": 7}
    entry = MockConfigEntry(domain=DOMAIN, data=data, unique_id=TEST_SERIAL, version=2)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    schema = result["data_schema"].schema
    device_id_key = next(key for key in schema if key == "device_id")
    assert device_id_key.default() == 7
