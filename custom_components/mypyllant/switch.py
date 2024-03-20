from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.const import DOMAIN, DEFAULT_HOLIDAY_SETPOINT
from custom_components.mypyllant.coordinator import SystemCoordinator
from custom_components.mypyllant.utils import (
    HolidayEntity,
    DomesticHotWaterCoordinatorEntity,
    EntityList,
)
from myPyllant.utils import get_default_holiday_dates

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

    sensors: EntityList[SwitchEntity] = EntityList()
    for index, system in enumerate(coordinator.data):
        sensors.append(lambda: SystemHolidaySwitch(index, coordinator, config))

        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            sensors.append(
                lambda: DomesticHotWaterBoostSwitch(index, dhw_index, coordinator)
            )
    async_add_entities(sensors)


class SystemHolidaySwitch(HolidayEntity, SwitchEntity):
    _attr_icon = "mdi:account-arrow-right"

    @property
    def name(self):
        return f"{self.name_prefix} Away Mode"

    @property
    def is_on(self):
        return self.zone.general.holiday_planned if self.zone else False

    async def async_turn_on(self, **kwargs):
        _, end = get_default_holiday_dates(
            self.holiday_start,
            self.holiday_end,
            self.system.timezone,
            self.default_holiday_duration,
        )
        setpoint = None
        if self.system.control_identifier.is_vrc700:
            setpoint = DEFAULT_HOLIDAY_SETPOINT
        await self.coordinator.api.set_holiday(self.system, end=end, setpoint=setpoint)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(20)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.cancel_holiday(self.system)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(20)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_switch"


class DomesticHotWaterBoostSwitch(DomesticHotWaterCoordinatorEntity, SwitchEntity):
    @property
    def name(self):
        return f"{self.name_prefix} Boost"

    @property
    def is_on(self):
        return self.domestic_hot_water.is_cylinder_boosting

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.boost_domestic_hot_water(
            self.domestic_hot_water,
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.cancel_hot_water_boost(
            self.domestic_hot_water,
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_boost_switch"
