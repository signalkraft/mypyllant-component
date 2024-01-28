from __future__ import annotations

import copy
import datetime
from typing import Any

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
    CalendarEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from myPyllant.models import (
    ZoneTimeProgramDay,
    ZoneTimeProgramType,
    BaseTimeProgram,
    BaseTimeProgramDay,
    DHWTimeProgramDay,
    DHWTimeProgram,
    ZoneTimeProgram,
)

from custom_components.mypyllant.const import WEEKDAYS_TO_RFC5545, RFC5545_TO_WEEKDAYS
from custom_components.mypyllant.entities.dhw import BaseDomesticHotWater
from custom_components.mypyllant.entities.zone import BaseZone


class BaseCalendarEntity(CalendarEntity):
    _attr_supported_features = (
        CalendarEntityFeature.CREATE_EVENT
        | CalendarEntityFeature.DELETE_EVENT
        | CalendarEntityFeature.UPDATE_EVENT
    )
    _has_setpoint = False

    @property
    def time_program(self) -> BaseTimeProgram:
        raise NotImplementedError

    @property
    def id_suffix(self):
        return self._get_calendar_id_prefix()

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

    def _get_rrule(self, time_program_day: BaseTimeProgramDay) -> str:
        matching_weekdays = self.time_program.matching_weekdays(time_program_day)
        return f"FREQ=WEEKLY;INTERVAL=1;BYDAY={','.join([WEEKDAYS_TO_RFC5545[d] for d in matching_weekdays])}"

    def _get_weekdays_from_rrule(self, rrule: str) -> list[str]:
        by_day = [p for p in rrule.split(";") if p.startswith("BYDAY=")][0].replace(
            "BYDAY=", ""
        )
        return [RFC5545_TO_WEEKDAYS[d] for d in by_day.split(",")]

    def get_setpoint_from_summary(self, summary: str):
        try:
            if " " in summary:
                summary = summary.split(" ")[0]
            return float(summary.replace("°C", ""))
        except ValueError:
            raise HomeAssistantError("Invalid setpoint, use format '21.5°C' in Summary")

    def _check_overlap(self):
        try:
            self.time_program.check_overlap()
        except ValueError as e:
            raise HomeAssistantError(str(e)) from e

    def build_event(
        self,
        time_program_day,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        raise NotImplementedError

    async def update_time_program(self):
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        start = datetime.datetime.now(self.system.timezone)
        end = start + datetime.timedelta(days=7)
        for time_program_day, start, end in self.time_program.as_datetime(start, end):
            return self.build_event(time_program_day, start, end)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        events = []
        for time_program_day, start, end in self.time_program.as_datetime(
            start_date, end_date
        ):
            events.append(self.build_event(time_program_day, start, end))
        return events

    async def async_create_event(self, **kwargs: Any) -> None:
        if "BYDAY=" not in kwargs["rrule"]:
            raise HomeAssistantError(
                "You need to select weekly repetition when planning a heating schedule"
            )
        start_time = (
            kwargs["dtstart"].time().hour * 60 + kwargs["dtstart"].time().minute
        )
        end_time = kwargs["dtend"].time().hour * 60 + kwargs["dtend"].time().minute
        for weekday in self._get_weekdays_from_rrule(kwargs["rrule"]):
            time_program_list = getattr(self.time_program, weekday)
            values = dict(
                index=len(time_program_list),
                weekday_name=weekday,
                start_time=start_time,
                end_time=end_time,
            )
            if self._has_setpoint:
                values["setpoint"] = self.get_setpoint_from_summary(kwargs["summary"])
            time_program_list.append(self.time_program.create_day_from_api(**values))

        self._check_overlap()
        await self.update_time_program()

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
        await self.update_time_program()

    async def async_update_event(
        self,
        uid: str,
        event: dict[str, Any],
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        if not recurrence_id or recurrence_range != "THISANDFUTURE":
            raise HomeAssistantError("You can only update all occurrences")
        if "BYDAY=" not in event["rrule"]:
            raise HomeAssistantError("You need to select weekly repetition")
        weekday, index, date = self._parse_uid(uid)
        if (
            event["dtstart"].date() != date.date()
            or event["dtend"].date() != date.date()
        ):
            raise HomeAssistantError(
                "You can only update the start and end time on the same day"
            )

        # Copy the updated day to compare other weekdays against
        try:
            time_program_day = copy.deepcopy(getattr(self.time_program, weekday)[index])
        except (IndexError, AttributeError) as e:
            raise HomeAssistantError("Time program was not found") from e
        start_time = event["dtstart"].time().hour * 60 + event["dtstart"].time().minute
        end_time = event["dtend"].time().hour * 60 + event["dtend"].time().minute
        for weekday in self._get_weekdays_from_rrule(event["rrule"]):
            # Only update matching day (same start / end / optionally setpoint)
            # Index might be different on other weekdays, so __eq__ is used
            matching_slots = [
                t for t in getattr(self.time_program, weekday) if t == time_program_day
            ]
            if matching_slots:
                # Updating matching day in self.time_program
                matching_slot = matching_slots[0]
                matching_slot.start_time = start_time
                matching_slot.end_time = end_time
                if self._has_setpoint:
                    matching_slot.setpoint = self.get_setpoint_from_summary(
                        event["summary"]
                    )
            else:
                # No matching day found on that day, adding new one
                values = dict(
                    index=len(getattr(self.time_program, weekday)),
                    weekday_name=weekday,
                    start_time=start_time,
                    end_time=end_time,
                )
                if self._has_setpoint:
                    values["setpoint"] = self.get_setpoint_from_summary(
                        event["summary"]
                    )
                getattr(self.time_program, weekday).append(
                    self.time_program.create_day_from_api(**values)
                )

        self._check_overlap()
        await self.update_time_program()


class ZoneHeatingCalendar(BaseCalendarEntity, BaseZone):
    _attr_icon = "mdi:thermometer-auto"
    _has_setpoint = True

    @property
    def time_program(self) -> ZoneTimeProgram:
        return self.zone.heating.time_program_heating

    @property
    def name_suffix(self) -> str:
        return "Heating Schedule"

    def _get_calendar_id_prefix(self):
        return f"zone_heating_{self.zone.index}"

    def build_event(
        self,
        time_program_day: ZoneTimeProgramDay,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        summary = f"{time_program_day.setpoint}°C on {self.name}"
        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description="You can change the start time, end time, weekdays, or the temperature in the Summary.",
            uid=self._get_uid(time_program_day, start),
            rrule=self._get_rrule(time_program_day),
            recurrence_id=self._get_recurrence_id(time_program_day),
        )

    async def update_time_program(self):
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
        time_program_day: DHWTimeProgramDay,
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        summary = f"{self.domestic_hot_water.tapping_setpoint}°C on {self.name}"
        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description="You can change the start time, end time, or weekdays.",
            uid=self._get_uid(time_program_day, start),
            rrule=self._get_rrule(time_program_day),
            recurrence_id=self._get_recurrence_id(time_program_day),
        )

    async def update_time_program(self):
        await self.coordinator.api.set_domestic_hot_water_time_program(
            self.domestic_hot_water, self.time_program
        )
        await self.coordinator.async_request_refresh_delayed()
