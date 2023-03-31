"""Sensors of ABB Power-One PVI SunSpec"""
import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback

from .const import (DOMAIN, INVERTER_TYPE, SENSOR_TYPES_SINGLE_PHASE,
                    SENSOR_TYPES_THREE_PHASE)
from .entity import ABBPowerOnePVISunSpecEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Setup sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    hub = coordinator.api
    sensors = []
    await coordinator.api.async_get_data()
    _LOGGER.debug("(sensor) Name: %s", entry.data[CONF_NAME])
    _LOGGER.debug("(sensor) Manufacturer: %s", hub.data["comm_manufact"])
    _LOGGER.debug("(sensor) Model: %s", hub.data["comm_model"])
    _LOGGER.debug("(sensor) SW Version: %s", hub.data["comm_version"])
    _LOGGER.debug("(sensor) Inverter Type (str): %s", hub.data["invtype"])
    _LOGGER.debug("(sensor) Serial#: %s", hub.data["comm_sernum"])
    if hub.data["invtype"] == INVERTER_TYPE[101]:
        for sensor_info in SENSOR_TYPES_SINGLE_PHASE.values():
            sensor_data = {
                "name": sensor_info[0],
                "key": sensor_info[1],
                "unit": sensor_info[2],
                "icon": sensor_info[3],
                "device_class": sensor_info[4],
                "state_class": sensor_info[5],
            }
            sensors.append(ABBPowerOnePVISunSpecSensor(coordinator, entry, sensor_data))
    elif hub.data["invtype"] == INVERTER_TYPE[103]:
        for sensor_info in SENSOR_TYPES_THREE_PHASE.values():
            sensor_data = {
                "name": sensor_info[0],
                "key": sensor_info[1],
                "unit": sensor_info[2],
                "icon": sensor_info[3],
                "device_class": sensor_info[4],
                "state_class": sensor_info[5],
            }
            sensors.append(ABBPowerOnePVISunSpecSensor(coordinator, entry, sensor_data))
    async_add_devices(sensors)
    return True


class ABBPowerOnePVISunSpecSensor(ABBPowerOnePVISunSpecEntity, SensorEntity):
    """Representation of an ABB SunSpec Modbus sensor"""

    def __init__(self, coordinator, config_entry, sensor_data):
        super().__init__(
            coordinator, config_entry, sensor_data
        )
        self._hub = coordinator.api
        self._device_name = config_entry.data[CONF_NAME]
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
