from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant import DOMAIN, SystemCoordinator
from custom_components.mypyllant.utils import (
    HolidayEntity,
    SystemCoordinatorEntity,
    ZoneCoordinatorEntity,
)

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
        sensors.append(SystemHolidayDurationNumber(index, coordinator))

        for zone_index, zone in enumerate(system.zones):
            sensors.append(ZoneQuickVetoDurationNumber(index, zone_index, coordinator))
    async_add_entities(sensors)


class SystemHolidayDurationNumber(HolidayEntity, NumberEntity):
    _attr_native_max_value = 365.0
    _attr_icon = "mdi:hvac-off"

    def __init__(self, index: int, coordinator: "SystemCoordinator") -> None:
        super(SystemCoordinatorEntity, self).__init__(coordinator)
        self.index = index

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        if (
            self.holiday_remaining
            and self.holiday_remaining.days > self._attr_native_max_value
        ):
            return self.holiday_remaining.days
        else:
            return self._attr_native_max_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """
        Switch to hours for short durations
        """
        if self.holiday_remaining and self.holiday_remaining.days < 1:
            return UnitOfTime.HOURS
        else:
            return UnitOfTime.DAYS

    @property
    def native_step(self) -> float | None:
        if self.native_unit_of_measurement == UnitOfTime.HOURS:
            return 0.1
        else:
            return super().native_step

    @property
    def name(self):
        return f"{self.name_prefix} Holiday Duration Remaining"

    @property
    def native_value(self):
        if self.holiday_remaining:
            if self.native_unit_of_measurement == UnitOfTime.DAYS:
                return round(self.holiday_remaining.total_seconds() / 3600 / 24)
            else:
                return round(self.holiday_remaining.total_seconds() / 3600)
        else:
            return 0

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_holiday(self.system)
            # Holiday values need a long time to show up in the API
            await self.coordinator.async_request_refresh_delayed(10)
        else:
            if self.native_unit_of_measurement == UnitOfTime.DAYS:
                value = value * 24
            end = datetime.now() + timedelta(hours=value)
            await self.coordinator.api.set_holiday(self.system, end=end)
            # Holiday values need a long time to show up in the API
            await self.coordinator.async_request_refresh_delayed(10)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_duration_remaining"


class ZoneQuickVetoDurationNumber(ZoneCoordinatorEntity, NumberEntity):
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:rocket-launch"

    @property
    def name(self):
        return f"{self.name_prefix} Quick Veto Duration"

    @property
    def native_value(self):
        return (
            round(self.zone.quick_veto_remaining.total_seconds() / 3600)
            if self.zone.quick_veto_remaining
            else 0
        )

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_quick_veto_zone_temperature(self.zone)
            await self.coordinator.async_request_refresh_delayed()
        else:
            await self.coordinator.api.quick_veto_zone_duration(self.zone, value)
            await self.coordinator.async_request_refresh_delayed()

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_quick_veto_duration"
