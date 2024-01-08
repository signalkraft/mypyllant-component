from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
    CalendarEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.coordinator import SystemCoordinator
from myPyllant.models import (
    ZoneTimeProgramDay,
    ZoneTimeProgramType,
    BaseTimeProgram,
    BaseTimeProgramDay,
    DHWTimeProgramDay,
    DHWTimeProgram,
    ZoneTimeProgram,
)

from .const import DOMAIN, WEEKDAYS_TO_RFC5545
from .entities.base import BaseSystemCoordinatorEntity
from .entities.dhw import BaseDomesticHotWater
from .entities.zone import BaseZone

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


class BaseCalendarEntity(BaseSystemCoordinatorEntity, CalendarEntity):
    _attr_supported_features = (
        CalendarEntityFeature.CREATE_EVENT
        | CalendarEntityFeature.DELETE_EVENT
        | CalendarEntityFeature.UPDATE_EVENT
    )

    @property
    def time_program(self) -> BaseTimeProgram:
        raise NotImplementedError

    def _get_calendar_id_prefix(self):
        raise NotImplementedError

    def _get_uid(self, time_program: BaseTimeProgramDay, date) -> str:
        return f"{self._get_calendar_id_prefix()}_{time_program.weekday_name}_{time_program.index}_{date.isoformat()}"

    def _parse_uid(self, recurrence_id: str) -> tuple[str, int, datetime.datetime]:
        weekday, index, date = recurrence_id.replace(
            f"{self._get_calendar_id_prefix()}_", ""
        ).split("_")
        return weekday, int(index), datetime.datetime.fromisoformat(date)

    def _get_recurrence_id(self, time_program: BaseTimeProgramDay) -> str:
        return f"{self._get_calendar_id_prefix()}_{time_program.weekday_name}_{time_program.index}"

    def _get_rrule(self, time_program: BaseTimeProgramDay) -> str:
        return f"FREQ=WEEKLY;INTERVAL=1;BYDAY={WEEKDAYS_TO_RFC5545[time_program.weekday_name]}"

    def build_event(
        self,
        time_program,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        start = datetime.datetime.now(self.system.timezone)
        end = start + datetime.timedelta(days=7)
        for time_program, start, end in self.time_program.as_datetime(start, end):
            return self.build_event(time_program, start, end)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        events = []
        _LOGGER.debug("Building events from %s - %s", start_date, end_date)
        for time_program, start, end in self.time_program.as_datetime(
            start_date, end_date
        ):
            events.append(self.build_event(time_program, start, end))
        return events


class ZoneHeatingCalendar(BaseCalendarEntity, BaseZone):
    _attr_icon = "mdi:thermometer-auto"

    @property
    def time_program(self) -> ZoneTimeProgram:
        return self.zone.heating.time_program_heating

    @property
    def name_suffix(self) -> str:
        return "Heating Schedule"

    def _get_calendar_id_prefix(self):
        return f"zone_heating_{self.zone.index}"

    def get_setpoint_from_summary(self, summary: str):
        try:
            if " " in summary:
                summary = summary.split(" ")[0]
            return float(summary.replace("°C", ""))
        except ValueError:
            raise HomeAssistantError("Invalid setpoint, use format '21.5°C' in Summary")

    def build_event(
        self,
        time_program: ZoneTimeProgramDay,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        summary = f"{time_program.setpoint}°C on {self.name}"
        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description="You can update the start time, end time, or the temperature in the Summary.",
            uid=self._get_uid(time_program, start),
            rrule=self._get_rrule(time_program),
            recurrence_id=self._get_recurrence_id(time_program),
        )

    async def async_create_event(self, **kwargs: Any) -> None:
        _LOGGER.debug("Creating zone heating event from %s", kwargs)
        setpoint = self.get_setpoint_from_summary(kwargs["summary"])
        weekday = kwargs["dtstart"].strftime("%A").lower()
        start_time = (
            kwargs["dtstart"].time().hour * 60 + kwargs["dtstart"].time().minute
        )
        end_time = kwargs["dtend"].time().hour * 60 + kwargs["dtend"].time().minute
        time_program_list = getattr(self.time_program, weekday)
        time_program_list.append(
            ZoneTimeProgramDay(
                index=len(time_program_list),
                weekday_name=weekday,
                start_time=start_time,
                end_time=end_time,
                setpoint=setpoint,
            )
        )
        await self.coordinator.api.set_zone_time_program(
            self.zone, str(ZoneTimeProgramType.HEATING), self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        if not recurrence_id or recurrence_range != "THISANDFUTURE":
            raise HomeAssistantError("You can only remove all occurrences")
        weekday, index, _ = self._parse_uid(uid)
        getattr(self.time_program, weekday).pop(index)
        await self.coordinator.api.set_zone_time_program(
            self.zone, str(ZoneTimeProgramType.HEATING), self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        if not recurrence_id or recurrence_range != "THISANDFUTURE":
            raise HomeAssistantError("You can only update all occurrences")
        weekday, index, date = self._parse_uid(uid)
        if (
            event["dtstart"].date() != date.date()
            or event["dtend"].date() != date.date()
        ):
            raise HomeAssistantError(
                "You can only update the start and end time on the same day"
            )
        time_program = getattr(self.time_program, weekday)[index]
        time_program.start_time = (
            event["dtstart"].time().hour * 60 + event["dtstart"].time().minute
        )
        time_program.end_time = (
            event["dtend"].time().hour * 60 + event["dtend"].time().minute
        )
        time_program.setpoint = self.get_setpoint_from_summary(event["summary"])
        await self.coordinator.api.set_zone_time_program(
            self.zone, str(ZoneTimeProgramType.HEATING), self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()


class DomesticHotWaterCalendar(BaseCalendarEntity, BaseDomesticHotWater):
    _attr_icon = "mdi:water-boiler-auto"

    @property
    def time_program(self) -> DHWTimeProgram:
        return self.domestic_hot_water.time_program_dhw

    @property
    def name_suffix(self) -> str:
        return "Schedule"

    def _get_calendar_id_prefix(self):
        return f"dhw_{self.domestic_hot_water.index}"

    def build_event(
        self,
        time_program: DHWTimeProgramDay,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        summary = f"{self.domestic_hot_water.tapping_setpoint}°C on {self.name}"
        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description="You can update the start time and end time.",
            uid=self._get_uid(time_program, start),
            rrule=self._get_rrule(time_program),
            recurrence_id=self._get_recurrence_id(time_program),
        )

    async def async_create_event(self, **kwargs: Any) -> None:
        if kwargs["dtstart"].date() != kwargs["dtend"].date():
            raise HomeAssistantError(
                "You can only plan time slots that start and end on the same day"
            )
        weekday = kwargs["dtstart"].strftime("%A").lower()
        start_time = (
            kwargs["dtstart"].time().hour * 60 + kwargs["dtstart"].time().minute
        )
        end_time = kwargs["dtend"].time().hour * 60 + kwargs["dtend"].time().minute
        time_program_list = getattr(self.time_program, weekday)
        time_program_list.append(
            DHWTimeProgramDay(
                index=len(time_program_list),
                weekday_name=weekday,
                start_time=start_time,
                end_time=end_time,
            )
        )
        await self.coordinator.api.set_domestic_hot_water_time_program(
            self.domestic_hot_water, self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        if not recurrence_id or recurrence_range != "THISANDFUTURE":
            raise HomeAssistantError("You can only remove all occurrences")
        weekday, index, _ = self._parse_uid(uid)
        getattr(self.time_program, weekday).pop(index)
        await self.coordinator.api.set_domestic_hot_water_time_program(
            self.domestic_hot_water, self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        if not recurrence_id or recurrence_range != "THISANDFUTURE":
            raise HomeAssistantError("You can only update all occurrences")
        weekday, index, date = self._parse_uid(uid)
        if (
            event["dtstart"].date() != date.date()
            or event["dtend"].date() != date.date()
        ):
            raise HomeAssistantError(
                "You can only update the start and end time on the same day"
            )
        time_program = getattr(self.time_program, weekday)[index]
        time_program.start_time = (
            event["dtstart"].time().hour * 60 + event["dtstart"].time().minute
        )
        time_program.end_time = (
            event["dtend"].time().hour * 60 + event["dtend"].time().minute
        )
        await self.coordinator.api.set_domestic_hot_water_time_program(
            self.domestic_hot_water, self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()
