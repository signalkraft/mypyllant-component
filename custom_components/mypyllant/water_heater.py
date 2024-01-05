import logging

import voluptuous as vol
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.entities.dhw import DomesticHotWaterEntity

from . import SystemCoordinator
from .const import (
    DOMAIN,
    SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM,
    SERVICE_SET_DHW_TIME_PROGRAM,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping water heater")
        return

    dhws: list[WaterHeaterEntity] = []

    for index, system in enumerate(coordinator.data):
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            dhws.append(DomesticHotWaterEntity(index, dhw_index, coordinator))

    async_add_entities(dhws)
    if len(dhws) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up water heater entity services for %s", platform)
        platform.async_register_entity_service(
            SERVICE_SET_DHW_TIME_PROGRAM,
            {
                vol.Required("time_program"): vol.All(dict),
            },
            "set_dhw_time_program",
        )
        platform.async_register_entity_service(
            SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM,
            {
                vol.Required("time_program"): vol.All(dict),
            },
            "set_dhw_circulation_time_program",
        )
