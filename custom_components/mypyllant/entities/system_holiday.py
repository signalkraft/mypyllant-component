from typing import Any, Mapping
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.number import NumberEntity
from custom_components.mypyllant.coordinator import SystemCoordinator

from custom_components.mypyllant.const import OPTION_DEFAULT_HOLIDAY_DURATION
from myPyllant.const import DEFAULT_HOLIDAY_DURATION
from homeassistant.config_entries import ConfigEntry
from datetime import datetime, timedelta
from homeassistant.const import UnitOfTime

from myPyllant.models import Zone
from myPyllant.utils import get_default_holiday_dates
from homeassistant.components.datetime import DateTimeEntity

from custom_components.mypyllant.entities.system import BaseSystem


class SystemHolidayBase(BaseSystem):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
        config: ConfigEntry,
    ) -> None:
        super().__init__(system_index, coordinator)
        if not self.system.zones:
            raise ValueError(
                f"System {self.system} requires zones for system holiday entities"
            )
        self.config = config

    @property
    def default_holiday_duration(self):
        return self.config.options.get(
            OPTION_DEFAULT_HOLIDAY_DURATION, DEFAULT_HOLIDAY_DURATION
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return {
            "holiday_ongoing": self.zone.general.holiday_ongoing,
            "holiday_remaining_seconds": self.zone.general.holiday_remaining.total_seconds()
            if self.zone.general.holiday_remaining
            else None,
            "holiday_start_date_time": self.holiday_start,
            "holiday_end_date_time": self.holiday_end,
        }

    @property
    def zone(self) -> Zone:
        return self.system.zones[0]

    @property
    def holiday_start(self) -> datetime | None:
        return (
            self.zone.general.holiday_start_date_time
            if self.zone.general.holiday_planned
            else None
        )

    @property
    def holiday_end(self) -> datetime | None:
        return (
            self.zone.general.holiday_end_date_time
            if self.zone.general.holiday_planned
            else None
        )

    @property
    def holiday_remaining(self) -> timedelta | None:
        return self.zone.general.holiday_remaining


class SystemHolidaySwitch(SystemHolidayBase, SwitchEntity):
    _attr_icon = "mdi:account-arrow-right"

    @property
    def id_suffix(self) -> str:
        return "holiday_switch"

    @property
    def name_suffix(self):
        return "Away Mode"

    @property
    def is_on(self):
        return self.zone.general.holiday_planned

    async def async_turn_on(self, **kwargs):
        _, end = get_default_holiday_dates(
            self.holiday_start,
            self.holiday_end,
            self.system.timezone,
            self.default_holiday_duration,
        )
        await self.coordinator.api.set_holiday(self.system, end=end)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.cancel_holiday(self.system)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)


class SystemHolidayDurationNumber(SystemHolidayBase, NumberEntity):
    _attr_native_max_value = 365.0
    _attr_icon = "mdi:hvac-off"

    @property
    def id_suffix(self) -> str:
        return "holiday_duration_remaining"

    @property
    def name_suffix(self):
        return "Holiday Duration Remaining"

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
            end = datetime.now(self.system.timezone) + timedelta(hours=value)
            await self.coordinator.api.set_holiday(self.system, end=end)
            # Holiday values need a long time to show up in the API
            await self.coordinator.async_request_refresh_delayed(10)


class SystemHolidayStartDateTimeEntity(SystemHolidayBase, DateTimeEntity):
    _attr_icon = "mdi:hvac"

    @property
    def id_suffix(self) -> str:
        return "holiday_start_date_time"

    @property
    def name_suffix(self):
        return "Away Mode Start Date"

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
        await self.coordinator.api.set_holiday(self.system, start=value, end=end)
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)


class SystemHolidayEndDateTimeEntity(SystemHolidayBase, DateTimeEntity):
    _attr_icon = "mdi:hvac-off"

    @property
    def name_suffix(self):
        return "Away Mode End Date"

    @property
    def id_suffix(self) -> str:
        return "holiday_end_date_time"

    @property
    def native_value(self):
        return (
            self.holiday_end.replace(tzinfo=self.system.timezone)
            if self.holiday_end
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        # TODO: Make API tz-aware
        await self.coordinator.api.set_holiday(
            self.system, start=self.holiday_start, end=value
        )
        # Holiday values need a long time to show up in the API
        await self.coordinator.async_request_refresh_delayed(10)
