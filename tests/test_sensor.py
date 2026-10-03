"""Sensor platform tests."""

from __future__ import annotations

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from modbus_connection import ModbusConnectionError
from modbus_connection.mock import MockModbusUnit
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.abb_powerone_pvi_sunspec.const import (
    DOMAIN,
    SENSOR_TYPES_COMMON,
    SENSOR_TYPES_SINGLE_MPPT,
)
from custom_components.abb_powerone_pvi_sunspec.sensor import ABBPowerOneFimerSensor
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

from .conftest import TEST_SERIAL
from .registers import InverterSpec, MpptSpec, build_register_map

SCAN_INTERVAL = timedelta(seconds=60)


def sensor_state(hass: HomeAssistant, key: str) -> State:
    """Return the state of the sensor for data key ``key``."""
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{TEST_SERIAL}_{key}")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def poll(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Advance to the next scheduled poll and let it finish."""
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_measurement_sensors(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Measurements carry their value, unit, device class and state class."""
    power = sensor_state(hass, "acpower")
    assert power.state == "4321"
    assert power.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    assert power.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert power.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert power.attributes[ATTR_ICON] == "mdi:solar-power"

    energy = sensor_state(hass, "totalenergy")
    assert energy.state == "12345678"
    assert energy.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING

    assert sensor_state(hass, "acfreq").state == "50.02"
    assert sensor_state(hass, "dc2power").state == "750"


async def test_information_sensors_are_diagnostic(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Identification and status sensors are diagnostic; measurements are not."""
    registry = er.async_get(hass)

    def category(key: str) -> EntityCategory | None:
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_SERIAL}_{key}")
        assert entity_id is not None
        entry = registry.async_get(entity_id)
        assert entry is not None
        return entry.entity_category

    assert sensor_state(hass, "comm_manufact").state == "Power-One"
    assert sensor_state(hass, "status").state == "Run"
    assert category("comm_sernum") is EntityCategory.DIAGNOSTIC
    assert category("status") is EntityCategory.DIAGNOSTIC
    assert category("acpower") is None


async def test_sensors_follow_polls(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """New readings reach the sensors; a failed poll makes them unavailable until it recovers."""
    mock_unit.holding.update(build_register_map(InverterSpec(ac_power=1000)))
    await poll(hass, freezer)
    assert sensor_state(hass, "acpower").state == "1000"

    mock_unit.fail_requests(ModbusConnectionError("no route to host"))
    await poll(hass, freezer)
    assert sensor_state(hass, "acpower").state == STATE_UNAVAILABLE

    mock_unit.fail_requests(None)
    await poll(hass, freezer)
    assert sensor_state(hass, "acpower").state == "1000"


async def test_single_phase_single_mppt_sensor_set(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_unit: MockModbusUnit
) -> None:
    """A single-phase, single-MPPT inverter gets only the sensors that apply to it."""
    mock_unit.holding.clear()
    mock_unit.holding.update(
        build_register_map(InverterSpec(invtype=101, mppts=[MpptSpec(100, 2000, 300)]))
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
    assert len(entities) == len(SENSOR_TYPES_COMMON) + len(SENSOR_TYPES_SINGLE_MPPT)
    assert sensor_state(hass, "dcvolt").state == "200.0"


async def test_value_missing_from_data(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A sensor whose key the inverter does not provide has no value."""
    coordinator = init_integration.runtime_data.coordinator
    sensor = ABBPowerOneFimerSensor(
        coordinator,
        {
            "name": "Missing",
            "key": "not_read",
            "unit": None,
            "icon": None,
            "device_class": None,
            "state_class": None,
        },
    )

    assert sensor.native_value is None
    assert sensor.unique_id == f"{TEST_SERIAL}_not_read"
    assert sensor.should_poll is False
