from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant import DOMAIN, SystemCoordinator
from custom_components.mypyllant.const import OPTION_DEFAULT_HOLIDAY_DURATION
from custom_components.mypyllant.utils import (
    HolidayEntity,
    DomesticHotWaterCoordinatorEntity,
)
from myPyllant.const import DEFAULT_HOLIDAY_DURATION
from myPyllant.models import DHWCurrentSpecialFunction
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

    default_holiday_duration = config.options.get(
        OPTION_DEFAULT_HOLIDAY_DURATION, DEFAULT_HOLIDAY_DURATION
    )

    sensors = []
    for index, system in enumerate(coordinator.data):
        sensors.append(
            SystemHolidaySwitch(index, coordinator, default_holiday_duration)
        )

        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            sensors.append(DomesticHotWaterBoostSwitch(index, dhw_index, coordinator))
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
            self.holiday_start, self.holiday_end, self.default_holiday_duration
        )
        await self.coordinator.api.set_holiday(self.system, end=end)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.cancel_holiday(self.system)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_switch"


class DomesticHotWaterBoostSwitch(DomesticHotWaterCoordinatorEntity, SwitchEntity):
    @property
    def name(self):
        return f"{self.name_prefix} Boost"

    @property
    def is_on(self):
        return (
            self.domestic_hot_water.current_special_function
            == DHWCurrentSpecialFunction.CYLINDER_BOOST
        )

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
