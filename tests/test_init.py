"""Setup, unload, device registry and migration tests."""

from __future__ import annotations

from unittest.mock import patch

from modbus_connection import ModbusConnectionError, ModbusTcpParams
from modbus_connection.mock import MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.abb_powerone_pvi_sunspec import async_remove_config_entry_device
from custom_components.abb_powerone_pvi_sunspec.const import (
    DOMAIN,
    SENSOR_TYPES_COMMON,
    SENSOR_TYPES_DUAL_MPPT,
    SENSOR_TYPES_THREE_PHASE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import TEST_HOST, TEST_SERIAL, USER_INPUT
from .registers import InverterSpec, build_register_map


async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """Setup takes a unit on the shared connection the entry describes, and unloads cleanly."""
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.abb_powerone_pvi_sunspec.async_get_unit", return_value=mock_unit
    ) as mock_get_unit:
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    _, entry, params, unit_id = mock_get_unit.call_args.args
    assert entry is config_entry
    assert params == ModbusTcpParams(host=TEST_HOST, port=502)
    assert unit_id == USER_INPUT["device_id"]

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_device_and_entities(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """The inverter is registered as one device carrying all three-phase dual-MPPT sensors."""
    assert init_integration.state is ConfigEntryState.LOADED

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, TEST_SERIAL), init_integration.entry_id
    )
    assert device is not None
    assert device.manufacturer == "Power-One"
    assert device.model == "PVI-10.0-OUTD"
    assert device.serial_number == TEST_SERIAL
    assert device.sw_version == "C008"
    assert device.name == USER_INPUT["name"]
    assert device.configuration_url == f"http://{TEST_HOST}"
    assert device.via_device_id is None

    entities = er.async_entries_for_config_entry(er.async_get(hass), init_integration.entry_id)
    expected = (
        len(SENSOR_TYPES_COMMON) + len(SENSOR_TYPES_THREE_PHASE) + len(SENSOR_TYPES_DUAL_MPPT)
    )
    assert len(entities) == expected
    assert all(entity.unique_id.startswith(f"{TEST_SERIAL}_") for entity in entities)


async def test_setup_retries_when_inverter_unreachable(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """A failed first poll leaves the entry in setup-retry instead of failing hard."""
    mock_unit.fail_requests(ModbusConnectionError("no route to host"))

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_retries_without_serial_number(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """An inverter answering with an empty serial number is retried, not set up."""
    mock_unit.holding.update(build_register_map(InverterSpec(serial="")))

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_fails_on_modbus_link_conflict(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Another integration holding the inverter with other link settings is a setup error."""
    config_entry.add_to_hass(hass)
    with patch(
        "custom_components.abb_powerone_pvi_sunspec.async_get_unit",
        side_effect=HomeAssistantError("already in use"),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert config_entry.reason is not None
    assert "already in use" in config_entry.reason


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


async def test_migrate_v1_with_device_id_keeps_it(hass: HomeAssistant) -> None:
    """A version 1 entry that already has device_id is only bumped to version 2."""
    entry = MockConfigEntry(
        domain=DOMAIN, title="old", data=dict(USER_INPUT), unique_id=TEST_SERIAL, version=1
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 2
    assert entry.data == USER_INPUT


@pytest.mark.parametrize(
    ("identifier", "removable"),
    [
        ((DOMAIN, TEST_SERIAL), False),
        (("other_domain", "abc"), True),
    ],
)
async def test_remove_config_entry_device(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    identifier: tuple[str, str],
    removable: bool,
) -> None:
    """The inverter device cannot be deleted on its own; the integration must be removed."""
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=init_integration.entry_id, identifiers={identifier}
    )

    assert await async_remove_config_entry_device(hass, init_integration, device) is removable
