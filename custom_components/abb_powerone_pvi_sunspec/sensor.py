"""Sensor Platform Device for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ABBPowerOneFimerConfigEntry
from .const import (
    CONF_NAME,
    DOMAIN,
    INVERTER_TYPE,
    SENSOR_TYPES_COMMON,
    SENSOR_TYPES_DUAL_MPPT,
    SENSOR_TYPES_SINGLE_MPPT,
    SENSOR_TYPES_SINGLE_PHASE,
    SENSOR_TYPES_THREE_PHASE,
)
from .coordinator import ABBPowerOneFimerCoordinator

_LOGGER = logging.getLogger(__name__)


def add_sensor_defs(
    coordinator: ABBPowerOneFimerCoordinator,
    config_entry: ABBPowerOneFimerConfigEntry,
    sensor_list,
    sensor_definitions,
):
    """Class Initializitation."""

    for sensor_info in sensor_definitions.values():
        sensor_data = {
            "name": sensor_info[0],
            "key": sensor_info[1],
            "unit": sensor_info[2],
            "icon": sensor_info[3],
            "device_class": sensor_info[4],
            "state_class": sensor_info[5],
        }
        sensor_list.append(ABBPowerOneFimerSensor(coordinator, sensor_data))


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ABBPowerOneFimerConfigEntry, async_add_entities
):
    """Sensor Platform setup."""

    # Get handler to coordinator from config
    coordinator: ABBPowerOneFimerCoordinator = config_entry.runtime_data.coordinator

    _LOGGER.debug(f"(sensor) Name: {config_entry.data.get(CONF_NAME)}")
    _LOGGER.debug(f"(sensor) Manufacturer: {coordinator.api.data['comm_manufact']}")
    _LOGGER.debug(f"(sensor) Model: {coordinator.api.data['comm_model']}")
    _LOGGER.debug(f"(sensor) SW Version: {coordinator.api.data['comm_version']}")
    _LOGGER.debug(f"(sensor) Inverter Type (str): {coordinator.api.data['invtype']}")
    _LOGGER.debug(f"(sensor) MPPT #: {coordinator.api.data['mppt_nr']}")
    _LOGGER.debug(f"(sensor) Serial#: {coordinator.api.data['comm_sernum']}")

    sensor_list = []
    add_sensor_defs(coordinator, config_entry, sensor_list, SENSOR_TYPES_COMMON)

    if coordinator.api.data["invtype"] == INVERTER_TYPE[101]:
        add_sensor_defs(
            coordinator, config_entry, sensor_list, SENSOR_TYPES_SINGLE_PHASE
        )
    elif coordinator.api.data["invtype"] == INVERTER_TYPE[103]:
        add_sensor_defs(
            coordinator, config_entry, sensor_list, SENSOR_TYPES_THREE_PHASE
        )

    _LOGGER.debug(
        f"(sensor) DC Voltages : single={coordinator.api.data['dcvolt']} dc1={coordinator.api.data['dc1volt']} dc2={coordinator.api.data['dc2volt']}"
    )
    if coordinator.api.data["mppt_nr"] == 1:
        add_sensor_defs(
            coordinator, config_entry, sensor_list, SENSOR_TYPES_SINGLE_MPPT
        )
    else:
        add_sensor_defs(coordinator, config_entry, sensor_list, SENSOR_TYPES_DUAL_MPPT)

    async_add_entities(sensor_list)

    return True


class ABBPowerOneFimerSensor(CoordinatorEntity, SensorEntity):
    """Representation of an ABB SunSpec Modbus sensor."""

    def __init__(self, coordinator, sensor_data):
        """Class Initializitation."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._name = sensor_data["name"]
        self._key = sensor_data["key"]
        self._unit_of_measurement = sensor_data["unit"]
        self._icon = sensor_data["icon"]
        self._device_class = sensor_data["device_class"]
        self._state_class = sensor_data["state_class"]
        self._device_name = self._coordinator.api.name
        self._device_host = self._coordinator.api.host
        self._device_model = self._coordinator.api.data["comm_model"]
        self._device_manufact = self._coordinator.api.data["comm_manufact"]
        self._device_sn = self._coordinator.api.data["comm_sernum"]
        self._device_swver = self._coordinator.api.data["comm_version"]
        self._device_hwver = self._coordinator.api.data["comm_options"]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        self._state = self._coordinator.api.data[self._key]
        self.async_write_ha_state()
        # write debug log only on first sensor to avoid spamming the log
        if self.name == "Manufacturer":
            _LOGGER.debug(
                "_handle_coordinator_update: sensors state written to state machine"
            )

    # when has_entity_name is True, the resulting entity name will be: {device_name}_{self._name}
    @property
    def has_entity_name(self):
        """Return the name state."""
        return True

    @property
    def name(self):
        """Return the name."""
        return f"{self._name}"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return the sensor icon."""
        return self._icon

    @property
    def device_class(self):
        """Return the sensor device_class."""
        return self._device_class

    @property
    def state_class(self):
        """Return the sensor state_class."""
        return self._state_class

    @property
    def entity_category(self):
        """Return the sensor entity_category."""
        if self._state_class is None:
            return EntityCategory.DIAGNOSTIC
        else:
            return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._key in self._coordinator.api.data:
            return self._coordinator.api.data[self._key]
        else:
            return None

    @property
    def state_attributes(self) -> dict[str, Any] | None:
        """Return the attributes."""
        return None

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._device_sn}_{self._key}"

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            "configuration_url": f"http://{self._device_host}",
            "hw_version": None,
            "identifiers": {(DOMAIN, self._device_sn)},
            "manufacturer": self._device_manufact,
            "model": self._device_model,
            "name": self._device_name,
            "serial_number": self._device_sn,
            "sw_version": self._device_swver,
            "via_device": None,
        }
