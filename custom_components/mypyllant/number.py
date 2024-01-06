from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant import DOMAIN, SystemCoordinator
from custom_components.mypyllant.entities.system_holiday import (
    SystemHolidayDurationNumber,
)
from custom_components.mypyllant.entities.zone import ZoneQuickVetoDurationNumber

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping number entities")
        return

    sensors = []
    for index, system in enumerate(coordinator.data):
        if system.zones:
            # Holiday entities require a zone
            sensors.append(SystemHolidayDurationNumber(index, coordinator, config))
        else:
            _LOGGER.info(
                "Skipping SystemHolidayDurationNumber, because there are no zones on %s",
                str(system),
            )

        for zone_index, zone in enumerate(system.zones):
            sensors.append(ZoneQuickVetoDurationNumber(index, zone_index, coordinator))
    async_add_entities(sensors)
