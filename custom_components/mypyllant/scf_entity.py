"""HA entities for scf systems, generated generically from the ScfPoints.

Read layer (sensor / binary sensor). Controls (number/select/switch with write endpoints)
follow separately.
"""

from __future__ import annotations

import re

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfPressure, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.coordinator import SystemCoordinator
from custom_components.mypyllant.scf import ScfPoint, ScfSystem
from custom_components.mypyllant.scf_write import patch_schedule, patch_value


def _human(text: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", text).strip().title()


class ScfEntity(CoordinatorEntity):
    """Base: holds system ID + point ID and reads the point fresh from the coordinator
    data on every access (so updates are reflected)."""

    coordinator: SystemCoordinator
    _attr_has_entity_name = True

    def __init__(self, coordinator: SystemCoordinator, point: ScfPoint) -> None:
        super().__init__(coordinator)
        self.system_id = point.system_id
        self.suffix = point.unique_suffix
        self._section = point.section
        self._key = point.key

    @property
    def _system(self) -> ScfSystem | None:
        for s in self.coordinator.scf_systems:
            if s.system_id == self.system_id:
                return s
        return None

    @property
    def point(self) -> ScfPoint | None:
        system = self._system
        if not system:
            return None
        for p in system.points:
            if p.unique_suffix == self.suffix:
                return p
        return None

    @property
    def available(self) -> bool:
        return self.point is not None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_scf_{self.system_id}_{self.suffix}"

    @property
    def name(self) -> str:
        return f"{self._section} {_human(self._key)}"

    @property
    def device_info(self) -> DeviceInfo:
        system = self._system
        return DeviceInfo(
            identifiers={(DOMAIN, f"scf_{self.system_id}")},
            name=system.home_name if system else "Vaillant iQconnect",
            manufacturer="Vaillant",
            model=system.nomenclature if system else "iQconnect",
        )


# --- Derive unit / device class from the field name -------------------------
_TEMP_RE = re.compile(r"temperature|setpoint", re.IGNORECASE)
_PRESS_RE = re.compile(r"pressure", re.IGNORECASE)


def _sensor_traits(key: str) -> tuple[str | None, str | None, str | None]:
    """(unit, device_class, state_class) heuristically from the field name."""
    if _PRESS_RE.search(key):
        return (
            UnitOfPressure.BAR,
            SensorDeviceClass.PRESSURE,
            SensorStateClass.MEASUREMENT,
        )
    if _TEMP_RE.search(key) and "mode" not in key.lower():
        return (
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
        )
    return None, None, None


_WEEKDAYS = [
    ("monday", "Mo"),
    ("tuesday", "Tu"),
    ("wednesday", "We"),
    ("thursday", "Th"),
    ("friday", "Fr"),
    ("saturday", "Sa"),
    ("sunday", "Su"),
]


def _hhmm(minutes) -> str:
    # Note: a single-type except on purpose. The repo's pinned ruff formatter rewrites
    # `except (A, B):` into the Python-2 `except A, B:`, which is a SyntaxError on import
    # (the root cause of issues #464/#452). isinstance guards the TypeError case instead.
    if not isinstance(minutes, (int, float, str)):
        return "?"
    try:
        m = int(minutes)
    except ValueError:
        return "?"
    return f"{m // 60:02d}:{m % 60:02d}"


def _day_slots(day_value) -> list[str]:
    """Slot list of a single day → ['05:30–06:00', …]."""
    out = []
    for slot in day_value or []:
        out.append(f"{_hhmm(slot.get('startTime'))}–{_hhmm(slot.get('endTime'))}")
    return out


def _schedule_by_day(value: dict) -> dict[str, list[str]]:
    """{MONDAY|monday: [...]} → {'Mo': ['05:30–06:00', …], …} (case-insensitive)."""
    lower = {str(k).lower(): v for k, v in (value or {}).items()}
    return {short: _day_slots(lower.get(name, [])) for name, short in _WEEKDAYS}


def _schedule_summary(by_day: dict[str, list[str]]) -> str:
    """Compact summary; consecutive days with an identical plan are merged into groups."""
    # group days with an identical plan, keeping order
    groups: list[tuple[list[str], list[str]]] = []
    for short, slots in by_day.items():
        if groups and groups[-1][1] == slots:
            groups[-1][0].append(short)
        else:
            groups.append(([short], slots))
    parts = []
    for days, slots in groups:
        rng = days[0] if len(days) == 1 else f"{days[0]}–{days[-1]}"
        parts.append(f"{rng}: {', '.join(slots) if slots else 'off'}")
    return " · ".join(parts)[:255]


class ScfSensor(ScfEntity, SensorEntity):
    def __init__(self, coordinator: SystemCoordinator, point: ScfPoint) -> None:
        super().__init__(coordinator, point)
        if not point.is_schedule:
            unit, device_class, state_class = _sensor_traits(point.key)
            self._attr_native_unit_of_measurement = unit
            self._attr_device_class = device_class
            self._attr_state_class = state_class

    @property
    def native_value(self):
        point = self.point
        if not point:
            return None
        if point.is_schedule:
            return _schedule_summary(_schedule_by_day(point.value))
        value = point.value
        if isinstance(value, float):
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self):
        point = self.point
        if point and point.is_schedule:
            # Full plan per day as attributes (for automations/detail view) plus the raw
            # slots (with setpoint) under "raw", so a weekly schedule can be read losslessly
            # and written back via scf_set_schedule.
            attrs = {day: slots for day, slots in _schedule_by_day(point.value).items()}
            attrs["raw"] = point.value
            return attrs
        return None

    async def set_schedule(self, schedule: dict) -> None:
        """Service mypyllant.scf_set_schedule — write a full weekly schedule."""
        point = self.point
        if not point or not point.is_schedule:
            raise HomeAssistantError(
                "scf_set_schedule: target is not a schedule sensor"
            )
        await patch_schedule(self.coordinator.api, point.path, self.system_id, schedule)
        await self.coordinator.async_request_refresh()


class ScfBinarySensor(ScfEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool | None:
        point = self.point
        return bool(point.value) if point else None


# --- Controls ----------------------------------------------------------------
class ScfWriteMixin:
    """Shared: write, then trigger a coordinator refresh."""

    async def _write(self, value) -> None:
        point = self.point  # type: ignore[attr-defined]
        if not point:
            return
        await patch_value(
            self.coordinator.api,  # type: ignore[attr-defined]
            point.path,
            self.system_id,  # type: ignore[attr-defined]
            value,
        )
        await self.coordinator.async_request_refresh()  # type: ignore[attr-defined]


class ScfNumber(ScfEntity, ScfWriteMixin, NumberEntity):
    def __init__(self, coordinator: SystemCoordinator, point: ScfPoint) -> None:
        super().__init__(coordinator, point)
        meta = point.metadata or {}
        if meta.get("minimum") is not None:
            self._attr_native_min_value = meta["minimum"]
        if meta.get("maximum") is not None:
            self._attr_native_max_value = meta["maximum"]
        if meta.get("stepSize"):
            self._attr_native_step = meta["stepSize"]
        unit, device_class, _ = _sensor_traits(point.key)
        self._attr_native_unit_of_measurement = unit
        if device_class:
            self._attr_device_class = device_class

    @property
    def native_value(self):
        point = self.point
        return point.value if point else None

    async def async_set_native_value(self, value: float) -> None:
        # send LONG fields (e.g. charge durations) as integers
        point = self.point
        if point and point.mtype == "LONG":
            value = int(value)
        await self._write(value)


class ScfSelect(ScfEntity, ScfWriteMixin, SelectEntity):
    def __init__(self, coordinator: SystemCoordinator, point: ScfPoint) -> None:
        super().__init__(coordinator, point)
        self._attr_options = (point.metadata or {}).get("allowedValues", [])

    @property
    def current_option(self):
        point = self.point
        return point.value if point else None

    async def async_select_option(self, option: str) -> None:
        await self._write(option)
