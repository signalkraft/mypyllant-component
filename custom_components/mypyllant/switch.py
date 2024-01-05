from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant import DOMAIN, SystemCoordinator
from custom_components.mypyllant.entities.dhw import DomesticHotWaterBoostSwitch
from custom_components.mypyllant.entities.system_holiday import SystemHolidaySwitch

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping switch entities")
        return

    sensors = []
    for index, system in enumerate(coordinator.data):
        sensors.append(SystemHolidaySwitch(index, coordinator, config))

        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            sensors.append(DomesticHotWaterBoostSwitch(index, dhw_index, coordinator))
    async_add_entities(sensors)
