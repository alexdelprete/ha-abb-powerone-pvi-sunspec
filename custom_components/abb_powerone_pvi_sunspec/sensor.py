"""Sensor Class of ABB Power-One PVI SunSpec"""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (DOMAIN, INVERTER_TYPE,
                    SENSOR_TYPES_COMMON,
                    SENSOR_TYPES_SINGLE_PHASE,
                    SENSOR_TYPES_THREE_PHASE,
                    SENSOR_TYPES_SINGLE_MPPT,
                    SENSOR_TYPES_DUAL_MPPT)
from .entity import ABBPowerOnePVISunSpecEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

def add_sensor_defs(coordinator, entry, sensors, definitions):
    for sensor_info in definitions.values():
        sensor_data = {
                "name": sensor_info[0],
                "key": sensor_info[1],
                "unit": sensor_info[2],
                "icon": sensor_info[3],
                "device_class": sensor_info[4],
                "state_class": sensor_info[5],
            }
        sensors.append(ABBPowerOnePVISunSpecSensor(coordinator, entry, sensor_data))

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Setup sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    hub = coordinator.api
    sensors = []
    _LOGGER.debug("(sensor) Name: %s", entry.data.get(CONF_NAME))
    _LOGGER.debug("(sensor) Manufacturer: %s", hub.data["comm_manufact"])
    _LOGGER.debug("(sensor) Model: %s", hub.data["comm_model"])
    _LOGGER.debug("(sensor) SW Version: %s", hub.data["comm_version"])
    _LOGGER.debug("(sensor) Inverter Type (str): %s", hub.data["invtype"])
    _LOGGER.debug("(sensor) MPPT #: %s", hub.data["mppt_nr"])
    _LOGGER.debug("(sensor) Serial#: %s", hub.data["comm_sernum"])

    add_sensor_defs(coordinator, entry, sensors, SENSOR_TYPES_COMMON);

    if hub.data["invtype"] == INVERTER_TYPE[101]:
        add_sensor_defs(coordinator, entry, sensors, SENSOR_TYPES_SINGLE_PHASE);
    elif hub.data["invtype"] == INVERTER_TYPE[103]:
        add_sensor_defs(coordinator, entry, sensors, SENSOR_TYPES_THREE_PHASE)

    # TODO: check if this check is good for all devices
    # I dont know if all multi mppt will return 0 but on mine this worked fine
    _LOGGER.debug("(sensor) DC Voltages : single=%d dc1=%d dc2=%d", hub.data["dcvolt"], hub.data["dc1volt"], hub.data["dc2volt"])
    if hub.data["mppt_nr"] == 1:
        add_sensor_defs(coordinator, entry, sensors, SENSOR_TYPES_SINGLE_MPPT)
    else:
        add_sensor_defs(coordinator, entry, sensors, SENSOR_TYPES_DUAL_MPPT)

    async_add_devices(sensors)

    return True


class ABBPowerOnePVISunSpecSensor(ABBPowerOnePVISunSpecEntity, SensorEntity):
    """Representation of an ABB SunSpec Modbus sensor"""

    def __init__(self, coordinator, config_entry, sensor_data):
        super().__init__(
            coordinator, config_entry, sensor_data
        )
        self._hub = coordinator.api
        self._device_name = config_entry.data.get(CONF_NAME)
        self._name = sensor_data["name"]
        self._key = sensor_data["key"]
        self._unit_of_measurement = sensor_data["unit"]
        self._icon = sensor_data["icon"]
        self._device_class = sensor_data["device_class"]
        self._state_class = sensor_data["state_class"]

    @property
    def has_entity_name(self):
        """Return the name"""
        return True

    @property
    def name(self):
        """Return the name"""
        return f"{self._name}"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement"""
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
    def native_value(self):
        """Return the state of the sensor."""
        if self._key in self._hub.data:
            return self._hub.data[self._key]

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the attributes"""
        return None

    @property
    def should_poll(self) -> bool:
        """Data is delivered by the hub"""
        return False
