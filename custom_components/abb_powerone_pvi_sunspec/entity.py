"""Entity Class of ABB Power-One PVI SunSpec."""

from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class ABBPowerOnePVISunSpecEntity(CoordinatorEntity):
    """Representation of an ABB SunSpec Modbus Entity."""

    def __init__(self, coordinator, config_entry, sensor_data):
        """Class Initializitation."""

        super().__init__(coordinator)
        self._coordinator = coordinator
        self._hub = coordinator.api
        self._config_entry = config_entry
        self._sensor_data = sensor_data
        self._device_name = self._config_entry.data.get(CONF_NAME)
        self._device_model = self._hub.data["comm_model"]
        self._device_manufact = self._hub.data["comm_manufact"]
        self._device_sn = self._hub.data["comm_sernum"]
        self._device_swver = self._hub.data["comm_version"]
        self._key = self._sensor_data["key"]

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._device_sn}_{self._key}"

    @property
    def device_info(self):
        """Return device attributes."""
        return {
            "identifiers": {(DOMAIN, self._device_sn)},
            "name": self._device_name,
            "model": self._device_model,
            "manufacturer": self._device_manufact,
            "sw_version": self._device_swver,
            "via_device": self._hub
        }
