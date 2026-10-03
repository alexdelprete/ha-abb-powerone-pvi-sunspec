"""Setup, unload and migration tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec.const import (
    DOMAIN,
    SENSOR_TYPES_COMMON,
    SENSOR_TYPES_DUAL_MPPT,
    SENSOR_TYPES_THREE_PHASE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import DEVICE_DATA, TEST_SERIAL, USER_INPUT


@pytest.mark.usefixtures("inverter_ok")
async def test_setup_and_unload(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """A three-phase dual-MPPT inverter loads, registers its device and sensors, and unloads."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, TEST_SERIAL), config_entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == DEVICE_DATA["comm_manufact"]
    assert device.model == DEVICE_DATA["comm_model"]
    assert device.serial_number == TEST_SERIAL

    entities = er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
    expected = (
        len(SENSOR_TYPES_COMMON) + len(SENSOR_TYPES_THREE_PHASE) + len(SENSOR_TYPES_DUAL_MPPT)
    )
    assert len(entities) == expected

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("inverter_unreachable")
async def test_setup_retries_when_inverter_unreachable(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A failed first poll leaves the entry in setup-retry instead of failing hard."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("inverter_ok")
async def test_migrate_v1_slave_id_to_device_id(hass: HomeAssistant) -> None:
    """Version 1 entries stored the Modbus unit id as slave_id; migration renames it."""
    v1_data = {k: v for k, v in USER_INPUT.items() if k != "device_id"} | {"slave_id": 7}
    entry = MockConfigEntry(
        domain=DOMAIN, title="old", data=v1_data, unique_id=TEST_SERIAL, version=1
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 2
    assert entry.data["device_id"] == 7
    assert "slave_id" not in entry.data
    assert entry.state is ConfigEntryState.LOADED
