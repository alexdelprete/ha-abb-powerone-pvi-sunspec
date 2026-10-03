"""Fixtures for the ABB/Power-One/FIMER PVI SunSpec tests.

The Modbus transport is never touched: ``ABBPowerOneFimerAPI.async_get_data`` is
replaced so the real API object, coordinator, config flow and sensor platform run
against a canned three-phase, dual-MPPT inverter.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.api import ABBPowerOneFimerAPI, VSNConnectionError
from custom_components.abb_powerone_pvi_sunspec.const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    INVERTER_TYPE,
)

TEST_SERIAL = "123456-3P75-1234"

USER_INPUT: dict[str, Any] = {
    CONF_NAME: "ABB Inverter",
    CONF_HOST: "192.168.1.50",
    CONF_PORT: 502,
    CONF_DEVICE_ID: 2,
    CONF_BASE_ADDR: 0,
    CONF_SCAN_INTERVAL: 60,
}

DEVICE_DATA: dict[str, Any] = {
    "comm_manufact": "Power-One",
    "comm_model": "PVI-10.0-OUTD",
    "comm_version": "C008",
    "comm_sernum": TEST_SERIAL,
    "comm_options": "DSP",
    "invtype": INVERTER_TYPE[103],
    "mppt_nr": 2,
    "acpower": 4321.0,
    "totalenergy": 12345678.0,
}


async def _get_data_ok(self: ABBPowerOneFimerAPI) -> bool:
    self.data.update(DEVICE_DATA)
    return True


async def _get_data_unreachable(self: ABBPowerOneFimerAPI) -> bool:
    raise VSNConnectionError("Failed to connect to inverter")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def inverter_ok() -> Generator[None]:
    """Inverter answers every poll with DEVICE_DATA."""
    with patch.object(ABBPowerOneFimerAPI, "async_get_data", _get_data_ok):
        yield


@pytest.fixture
def inverter_unreachable() -> Generator[None]:
    """Inverter never answers."""
    with patch.object(ABBPowerOneFimerAPI, "async_get_data", _get_data_unreachable):
        yield


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A current (version 2) config entry for the canned inverter."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=USER_INPUT[CONF_NAME],
        data=dict(USER_INPUT),
        unique_id=TEST_SERIAL,
        version=2,
    )
