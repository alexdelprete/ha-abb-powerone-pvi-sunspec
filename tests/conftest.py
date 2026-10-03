"""Fixtures for the ABB/Power-One/FIMER PVI SunSpec tests.

The integration takes a unit on Home Assistant's shared Modbus connection. Here
that unit is a ``MockModbusUnit`` serving the SunSpec register map of a canned
three-phase, dual-MPPT inverter, so the real API, coordinator, config flow and
sensor platform run end to end without a network.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from .registers import InverterSpec, build_register_map

TEST_SERIAL = InverterSpec().serial
TEST_HOST = "192.168.1.50"

USER_INPUT: dict[str, Any] = {
    CONF_NAME: "ABB Inverter",
    CONF_HOST: TEST_HOST,
    CONF_PORT: 502,
    CONF_DEVICE_ID: 2,
    CONF_BASE_ADDR: 0,
    CONF_SCAN_INTERVAL: 60,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def mock_unit() -> MockModbusUnit:
    """A mock Modbus unit serving the test inverter's register map."""
    unit = MockModbusConnection().for_unit(USER_INPUT[CONF_DEVICE_ID])
    unit.holding.update(build_register_map())
    return unit


@pytest.fixture(autouse=True)
def mock_shared_connection(mock_unit: MockModbusUnit) -> Generator[None]:
    """Hand out the mock unit in place of core's shared Modbus connection."""

    @asynccontextmanager
    async def temporary_unit(*args: Any, **kwargs: Any) -> AsyncIterator[MockModbusUnit]:
        yield mock_unit

    with (
        patch("custom_components.abb_powerone_pvi_sunspec.async_get_unit", return_value=mock_unit),
        patch(
            "custom_components.abb_powerone_pvi_sunspec.config_flow.async_get_temporary_unit",
            temporary_unit,
        ),
    ):
        yield


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A current (version 2) config entry for the test inverter."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=USER_INPUT[CONF_NAME],
        data=dict(USER_INPUT),
        unique_id=TEST_SERIAL,
        version=2,
    )


@pytest.fixture
async def init_integration(hass: HomeAssistant, config_entry: MockConfigEntry) -> MockConfigEntry:
    """Set up the integration with the test inverter."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
