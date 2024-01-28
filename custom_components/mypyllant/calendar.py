from __future__ import annotations

import logging

from homeassistant.components.calendar import (
    CalendarEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.entities.calendar import (
    DomesticHotWaterCalendar,
    ZoneHeatingCalendar,
)


from . import SystemCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping calendar entities")
        return

    sensors: list[CalendarEntity] = []
    for index, system in enumerate(coordinator.data):
        for zone_index, zone in enumerate(system.zones):
            sensors.append(ZoneHeatingCalendar(index, zone_index, coordinator))
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            sensors.append(DomesticHotWaterCalendar(index, dhw_index, coordinator))
    async_add_entities(sensors)
