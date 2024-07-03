from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.const import DOMAIN, DEFAULT_HOLIDAY_SETPOINT
from custom_components.mypyllant.coordinator import SystemCoordinator
from custom_components.mypyllant.utils import (
    HolidayEntity,
    EntityList,
    ManualCoolingEntity,
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
        _LOGGER.warning("No system data, skipping date time entities")
        return

    sensors: EntityList[DateTimeEntity] = EntityList()
    for index, system in enumerate(coordinator.data):
        sensors.append(
            lambda: SystemHolidayStartDateTimeEntity(index, coordinator, config)
        )
        sensors.append(
            lambda: SystemHolidayEndDateTimeEntity(index, coordinator, config)
        )
        if not system.control_identifier.is_vrc700 and system.is_cooling_allowed:
            sensors.append(
                lambda: SystemManualCoolingStartDateTimeEntity(
                    index, coordinator, config
                )
            )
            sensors.append(
                lambda: SystemManualCoolingEndDateTimeEntity(index, coordinator, config)
            )
    async_add_entities(sensors)  # type: ignore


class SystemHolidayStartDateTimeEntity(HolidayEntity, DateTimeEntity):
    _attr_icon = "mdi:hvac"

    @property
    def name(self):
        return f"{self.name_prefix} Away Mode Start Date"

    @property
    def native_value(self):
        return (
            self.holiday_start.replace(tzinfo=self.system.timezone)
            if self.holiday_start
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        _, end = get_default_holiday_dates(
            self.holiday_start,
            self.holiday_end,
            self.system.timezone,
            self.default_holiday_duration,
        )
        setpoint = None
        if self.system.control_identifier.is_vrc700:
            setpoint = DEFAULT_HOLIDAY_SETPOINT
        await self.coordinator.api.set_holiday(
            self.system, start=value, end=end, setpoint=setpoint
        )
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_start_date_time"


class SystemHolidayEndDateTimeEntity(SystemHolidayStartDateTimeEntity):
    _attr_icon = "mdi:hvac-off"

    @property
    def name(self):
        return f"{self.name_prefix} Away Mode End Date"

    @property
    def native_value(self):
        return (
            self.holiday_end.replace(tzinfo=self.system.timezone)
            if self.holiday_end
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        # TODO: Make API tz-aware
        setpoint = None
        if self.system.control_identifier.is_vrc700:
            setpoint = DEFAULT_HOLIDAY_SETPOINT
        await self.coordinator.api.set_holiday(
            self.system, start=self.holiday_start, end=value, setpoint=setpoint
        )
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_end_date_time"


class SystemManualCoolingStartDateTimeEntity(ManualCoolingEntity, DateTimeEntity):
    _attr_icon = "mdi:snowflake-check"

    @property
    def name(self):
        return f"{self.name_prefix} Manual Cooling Start Date"

    @property
    def native_value(self):
        return (
            self.manual_cooling_start.replace(tzinfo=self.system.timezone)
            if self.manual_cooling_start
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        _, end = get_default_holiday_dates(
            self.manual_cooling_start,
            self.manual_cooling_end,
            self.system.timezone,
            self.default_manual_cooling_duration,
        )
        await self.coordinator.api.set_cooling_for_days(
            self.system,
            start=value,
            end=end,
        )
        await self.coordinator.async_request_refresh_delayed(20)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_manual_cooling_start_date_time"


class SystemManualCoolingEndDateTimeEntity(SystemManualCoolingStartDateTimeEntity):
    _attr_icon = "mdi:snowflake-off"

    @property
    def name(self):
        return f"{self.name_prefix} Manual Cooling End Date"

    @property
    def native_value(self):
        return (
            self.manual_cooling_end.replace(tzinfo=self.system.timezone)
            if self.manual_cooling_end
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        await self.coordinator.api.set_cooling_for_days(
            self.system,
            start=self.manual_cooling_start,
            end=value,
        )
        await self.coordinator.async_request_refresh_delayed(20)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_manual_cooling_end_date_time"
