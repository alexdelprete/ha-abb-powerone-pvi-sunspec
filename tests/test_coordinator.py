"""Coordinator tests: polling interval and error handling."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from modbus_connection import IllegalDataAddressError, ModbusConnectionError, ModbusTimeoutError
from modbus_connection.mock import MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.api import ABBPowerOneFimerAPI
from custom_components.abb_powerone_pvi_sunspec.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from custom_components.abb_powerone_pvi_sunspec.coordinator import ABBPowerOneFimerCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .conftest import TEST_SERIAL, USER_INPUT


def make_coordinator(
    hass: HomeAssistant, unit: MockModbusUnit, **data_overrides: object
) -> ABBPowerOneFimerCoordinator:
    """Return a coordinator for an entry with ``data_overrides`` applied to its data."""
    data: dict[str, Any] = {
        key: value for key, value in {**USER_INPUT, **data_overrides}.items() if value is not None
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data, unique_id=TEST_SERIAL, version=2)
    entry.add_to_hass(hass)
    api = ABBPowerOneFimerAPI("Inverter", data["host"], unit, data["base_addr"])
    return ABBPowerOneFimerCoordinator(hass, entry, api)


@pytest.mark.parametrize(
    ("scan_interval", "expected"),
    [
        (120, 120),
        (5, MIN_SCAN_INTERVAL),
        (5000, MAX_SCAN_INTERVAL),
        (None, DEFAULT_SCAN_INTERVAL),
    ],
)
async def test_update_interval(
    hass: HomeAssistant, mock_unit: MockModbusUnit, scan_interval: int | None, expected: int
) -> None:
    """The configured scan interval is clamped to its bounds, with a default when missing."""
    coordinator = make_coordinator(hass, mock_unit, **{CONF_SCAN_INTERVAL: scan_interval})

    assert coordinator.update_interval == timedelta(seconds=expected)


async def test_update_returns_inverter_data(hass: HomeAssistant, mock_unit: MockModbusUnit) -> None:
    """A successful poll returns the API's data dict."""
    coordinator = make_coordinator(hass, mock_unit)

    data = await coordinator._async_update_data()

    assert data is coordinator.api.data
    assert data["comm_sernum"] == TEST_SERIAL


@pytest.mark.parametrize(
    "error",
    [
        ModbusConnectionError("no route to host"),
        ModbusTimeoutError("timed out"),
        IllegalDataAddressError(),
        ConnectionResetError("reset by peer"),
    ],
)
async def test_update_failure_raises_update_failed(
    hass: HomeAssistant, mock_unit: MockModbusUnit, error: Exception
) -> None:
    """Any failure to read the inverter becomes a translated UpdateFailed with its cause."""
    coordinator = make_coordinator(hass, mock_unit)
    mock_unit.fail_requests(error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert exc_info.value.translation_domain == DOMAIN
    assert exc_info.value.translation_key == "update_failed"
    assert exc_info.value.translation_placeholders == {"name": "Inverter", "error": str(error)}
    assert exc_info.value.__cause__ is error
