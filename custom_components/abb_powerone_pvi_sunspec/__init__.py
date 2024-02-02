"""ABB Power-One PVI SunSpec Integration.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_NAME,
    DATA,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    UPDATE_LISTENER,
)
from .coordinator import HubDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_instance_count(hass: HomeAssistant) -> int:
    """Return number of instances."""
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if not entry.disabled_by
    ]
    return len(entries)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    _LOGGER.debug("Setup config_entry for ABB")
    coordinator = HubDataUpdateCoordinator(hass, config_entry)
    # If the refresh fails, async_config_entry_first_refresh() will
    # raise ConfigEntryNotReady and setup will try again later
    # ref.: https://developers.home-assistant.io/docs/integration_setup_failures
    await coordinator.async_config_entry_first_refresh()
    hub = coordinator.api
    if not hub.data["comm_sernum"]:
        raise ConfigEntryNotReady

    # Update listener for config option changes
    update_listener = config_entry.add_update_listener(_async_update_listener)

    hass.data[DOMAIN][config_entry.entry_id] = {
        DATA: coordinator,
        UPDATE_LISTENER: update_listener,
    }

    # Setup platforms
    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    # Add hub as device
    await async_update_device_registry(hass, config_entry)

    return True


async def async_update_device_registry(hass: HomeAssistant, config_entry):
    """Update device registry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]
    hub = coordinator.api
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        hw_version=hub.data["comm_options"],
        identifiers={(DOMAIN, hub.data["comm_sernum"])},
        manufacturer=hub.data["comm_manufact"],
        model=hub.data["comm_model"],
        name=config_entry.data.get(CONF_NAME),
        serial_number=hub.data["comm_sernum"],
        sw_version=hub.data["comm_version"],
        via_device=(DOMAIN, hub.data["comm_sernum"]),
    )


async def _async_update_listener(hass: HomeAssistant, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry, device_entry
) -> bool:
    """Delete device if not entities."""
    if DOMAIN in device_entry.identifiers:
        _LOGGER.error(
            "You cannot delete the device using device delete. Remove the integration instead."
        )
        return False
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle removal of config_entry."""

    _LOGGER.debug("Unload config_entry")
    if get_instance_count(hass) == 0:
        # Unload lovelace module resource if only instance
        _LOGGER.debug("Unload config_entry: no more entries found")

    _LOGGER.debug("Unload integration platforms")
    # Unload a config entry
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    _LOGGER.debug("Detach config update listener")
    hass.data[DOMAIN][config_entry.entry_id][UPDATE_LISTENER]()

    if unloaded:
        _LOGGER.debug("Unload integration")
        hass.data[DOMAIN].pop(config_entry.entry_id)
        return True  # unloaded
    else:
        _LOGGER.debug("Unload config_entry failed: integration not unloaded")
        return False  # unload failed


# async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
#     """Migrate an old config_entry."""
#     version = config_entry.version

#     # 1-> 2: Migration format
#     if version == 1:
#         hub_name = config_entry.data.get(CONF_NAME)
#         hub = hass.data[DOMAIN][hub_name]["hub"]
#         # hub.read_sunspec_modbus_init()
#         # hub.read_sunspec_modbus_data()
#         _LOGGER.debug("Migrating from version %s", version)
#         old_uid = config_entry.unique_id
#         new_uid = hub.data["comm_sernum"]
#         if old_uid != new_uid:
#             hass.config_entries.async_update_entry(
#                 config_entry, unique_id=new_uid
#             )
#             _LOGGER.debug("Migration to version %s complete: OLD_UID: %s - NEW_UID: %s", config_entry.version, old_uid, new_uid)
#         if config_entry.unique_id == new_uid:
#             config_entry.version = 2
#             _LOGGER.debug("Migration to version %s complete: NEW_UID: %s", config_entry.version, config_entry.unique_id)
#     return True
