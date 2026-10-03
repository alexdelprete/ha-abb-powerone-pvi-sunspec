"""ABB Power-One PVI SunSpec Integration.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

from dataclasses import dataclass
import logging

from modbus_connection import ModbusTcpParams

from homeassistant.components.modbus import async_get_unit
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .api import ABBPowerOneFimerAPI
from .const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    DOMAIN,
    STARTUP_MESSAGE,
)
from .coordinator import ABBPowerOneFimerCoordinator
from .helpers import log_debug, log_error, log_info

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# The type alias needs to be suffixed with 'ConfigEntry'
type ABBPowerOneFimerConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: ABBPowerOneFimerCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: ABBPowerOneFimerConfigEntry):
    """Set up this integration using UI."""
    log_info(_LOGGER, "async_setup_entry", STARTUP_MESSAGE)
    log_debug(_LOGGER, "async_setup_entry", "Setup config_entry", domain=DOMAIN)

    data = config_entry.data
    # A unit on Home Assistant's shared Modbus connection to the inverter: the
    # hold is released when the entry unloads, closing the link behind the last one
    params = ModbusTcpParams(host=data[CONF_HOST], port=int(data[CONF_PORT]))
    try:
        unit = async_get_unit(hass, config_entry, params, int(data[CONF_DEVICE_ID]))
    except HomeAssistantError as err:
        # another integration holds this device with different link settings
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="modbus_link_conflict",
            translation_placeholders={"host": data[CONF_HOST], "error": str(err)},
        ) from err

    api = ABBPowerOneFimerAPI(
        data.get(CONF_NAME, config_entry.title), data[CONF_HOST], unit, data[CONF_BASE_ADDR]
    )
    coordinator = ABBPowerOneFimerCoordinator(hass, config_entry, api)

    # If the refresh fails, async_config_entry_first_refresh() will
    # raise ConfigEntryNotReady and setup will try again later
    # ref.: https://developers.home-assistant.io/docs/integration_setup_failures
    await coordinator.async_config_entry_first_refresh()

    # Test to see if api initialised correctly, else raise ConfigNotReady to make HA retry setup
    # Change this to match how your api will know if connected or successful update
    if not coordinator.api.data["comm_sernum"]:
        raise ConfigEntryNotReady(f"Timeout connecting to {config_entry.data.get(CONF_NAME)}")

    # Store coordinator in runtime_data to make it accessible throughout the integration
    config_entry.runtime_data = RuntimeData(coordinator)

    # Register an update listener for config flow options changes
    # Listener is attached when entry loads and automatically detached at unload
    # ref.: https://developers.home-assistant.io/docs/config_entries_options_flow_handler/#signal-updates
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Register device
    async_update_device_registry(hass, config_entry)

    # Return true to denote a successful setup.
    return True


@callback
def async_update_device_registry(
    hass: HomeAssistant, config_entry: ABBPowerOneFimerConfigEntry
) -> None:
    """Manual device registration."""
    coordinator: ABBPowerOneFimerCoordinator = config_entry.runtime_data.coordinator
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        hw_version=None,
        configuration_url=f"http://{config_entry.data.get(CONF_HOST)}",
        identifiers={(DOMAIN, coordinator.api.data["comm_sernum"])},
        manufacturer=coordinator.api.data["comm_manufact"],
        model=coordinator.api.data["comm_model"],
        name=config_entry.data.get(CONF_NAME),
        serial_number=coordinator.api.data["comm_sernum"],
        sw_version=coordinator.api.data["comm_version"],
    )


async def async_remove_config_entry_device(hass: HomeAssistant, config_entry, device_entry) -> bool:
    """Delete device if not entities."""
    if any(identifier[0] == DOMAIN for identifier in device_entry.identifiers):
        log_error(
            _LOGGER,
            "async_remove_config_entry_device",
            "You cannot delete the device using device delete. Remove the integration instead.",
        )
        return False
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: ABBPowerOneFimerConfigEntry
) -> bool:
    """Unload a config entry."""
    log_debug(_LOGGER, "async_unload_entry", "Unload config_entry: started")

    # The shared Modbus connection is released by the hold taken in setup
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    log_debug(
        _LOGGER,
        "async_unload_entry",
        "Unload config_entry: completed",
        unload_ok=unload_ok,
    )
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, config_entry: ABBPowerOneFimerConfigEntry
) -> None:
    """Reload the config entry."""
    hass.config_entries.async_schedule_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old config entries."""
    log_debug(
        _LOGGER,
        "async_migrate_entry",
        "Migrating config entry",
        version=config_entry.version,
    )

    if config_entry.version == 1:
        # Version 1 -> 2: Migrate slave_id to device_id
        new_data = {**config_entry.data}

        # If slave_id exists but device_id doesn't, migrate it
        if "slave_id" in new_data and "device_id" not in new_data:
            new_data["device_id"] = new_data.pop("slave_id")
            log_info(
                _LOGGER,
                "async_migrate_entry",
                "Migrated slave_id to device_id in config entry",
            )

        # Update the config entry
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)
        log_debug(_LOGGER, "async_migrate_entry", "Migration to version 2 complete")

    return True
