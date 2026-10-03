"""Config and options flow tests."""

from __future__ import annotations

import pytest
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

from .conftest import TEST_SERIAL, USER_INPUT


async def test_user_form_is_shown(hass: HomeAssistant) -> None:
    """The user step starts with an empty form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.usefixtures("inverter_ok")
async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """A reachable inverter creates an entry keyed by its serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=dict(USER_INPUT)
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT["name"]
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == TEST_SERIAL


@pytest.mark.usefixtures("inverter_unreachable")
async def test_user_flow_unreachable_inverter(hass: HomeAssistant) -> None:
    """An unreachable inverter keeps the form open with a host error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=dict(USER_INPUT)
    )
    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_invalid_host(hass: HomeAssistant) -> None:
    """A malformed host is rejected before any connection attempt."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={**USER_INPUT, CONF_HOST: "not a host!"},
    )
    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


async def test_user_flow_host_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """The same host cannot be added twice."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=dict(USER_INPUT)
    )
    assert result["type"] is FlowResultType.FORM
    assert CONF_HOST in result["errors"]


@pytest.mark.usefixtures("inverter_ok")
async def test_options_flow_updates_entry_and_reloads(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Saving options rewrites the entry data and reloads it cleanly.

    Regression test: the update listener used to be a plain function, which
    HA 2026.9 schedules as a task, so saving options handed it None.
    """
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
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

    assert config_entry.data[CONF_PORT] == 1502
    assert config_entry.data[CONF_SCAN_INTERVAL] == 120
    assert config_entry.data["name"] == USER_INPUT["name"]
    assert config_entry.state is ConfigEntryState.LOADED
