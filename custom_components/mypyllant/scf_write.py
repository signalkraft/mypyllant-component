"""Write mapping for scf controls.

Every entry is verified from the app decompilation: the app branches explicitly on
`controlIdentifier === 'scf'` and, for scf, calls the endpoints listed here (all under the
`system-control/v1` base, the same one the state comes from) with the given body field.

Kept deliberately SMALL: only fields whose endpoint+body are firmly established. Everything
else stays a read-only sensor for now (see scf.py). Extend as further endpoints are confirmed
via the no-op test.

Payload evidence (decompilation):
  setDomesticHotWaterCylinderTemperature → PATCH .../domestic-hot-water/{i}/cylinder-temperature  {"setpoint": <float>}
  setZoneOperationMode                   → PATCH .../zones/{i}/operation-mode                     {"operationMode": <enum>}
"""

from __future__ import annotations

import logging

from myPyllant.const import SYSTEM_CONTROL_API_URL_BASE

_LOGGER = logging.getLogger(__name__)

# All confirmed scf write paths live under system-control/v1 — the same base as the state
# read. (/scf/v1 and the /{controlIdentifier}/v1 OpenAPI path both return 404; verified via
# no-op test on the device, 2026-07-17.)
# Key: (top_section, subsection, leaf_key). subsection = path[2] for indexed sections
# (zone/circuit/dhw), path[1] for systemParameters.
# Value: (endpoint_template, body_key). {i} = index from path[1].
WRITE_MAP: dict[tuple[str, str, str], tuple[str, str]] = {
    ("domesticHotWaterSettings", "configuration", "cylinderTemperatureSetpoint"): (
        "domestic-hot-water/{i}/cylinder-temperature",
        "setpoint",
    ),
    ("domesticHotWaterSettings", "configuration", "operationMode"): (
        "domestic-hot-water/{i}/operation-mode",
        "operationMode",
    ),
    ("zoneSettings", "general", "operationMode"): (
        "zones/{i}/operation-mode",
        "operationMode",
    ),
    ("zoneSettings", "heating", "manualModeTemperatureSetpoint"): (
        "zones/{i}/heating-temperature-setpoint",
        "setpoint",
    ),
    # Heating circuit: the path is system-control/v1/.../CIRCUITS (plural!) — found via a
    # no-op probe (2026-07-17: circuits/1/heating-curve {heatingCurve} → 202 Accepted).
    # circuit (singular, from the OpenAPI client) and /scf/v1 both return 404.
    ("circuitSettings", "configuration", "heatingCurve"): (
        "circuits/{i}/heating-curve",
        "heatingCurve",
    ),
    # Further heating-circuit setpoints (min/max flow, offsets) very likely also live under
    # circuits/{i}/... — but the body key is still untested, so only add them after a no-op
    # test of your own (they remain read-only sensors until then).
}


def _base_url(system_id: str) -> str:
    return f"{SYSTEM_CONTROL_API_URL_BASE}/systems/{system_id}"


def map_key(path: list[str]) -> tuple[str, str, str] | None:
    """(top, subsection, leaf) from a point path; None if too short."""
    if len(path) < 3:
        return None
    top = path[0]
    if top == "systemParameters":
        return (top, path[1], path[-1])
    # indexed sections: path = [top, index, subsection, ..., leaf]
    if len(path) >= 4:
        return (top, path[2], path[-1])
    return None


def write_spec(path: list[str]) -> tuple[str, str] | None:
    """(endpoint_template, body_key) for a point, or None if not writable."""
    key = map_key(path)
    return WRITE_MAP.get(key) if key else None


def build_url(path: list[str], system_id: str) -> str | None:
    spec = write_spec(path)
    if not spec:
        return None
    endpoint_template, _ = spec
    index = path[1] if len(path) >= 2 else ""
    suffix = endpoint_template.format(i=index)
    return f"{_base_url(system_id)}/{suffix}"


async def patch_value(api, path: list[str], system_id: str, value) -> None:
    """PATCH the value to the mapped endpoint. Raises on HTTP error."""
    spec = write_spec(path)
    url = build_url(path, system_id)
    if not spec or not url:
        raise ValueError(f"No write endpoint for {path}")
    _, body_key = spec
    body = {body_key: value}
    _LOGGER.debug("scf PATCH %s %s", url, body)
    async with api.aiohttp_session.patch(
        url, json=body, headers=api.get_authorized_headers()
    ) as resp:
        resp.raise_for_status()


# --- Weekly schedules (TIME_PERIODS) ----------------------------------------
#
# Deliberately kept SEPARATE from WRITE_MAP: schedules stay read-only sensors
# (scf.py: platform()/has_write untouched) and are written exclusively through the
# service mypyllant.scf_set_schedule. The body is NOT {key: value} but the full per-day
# dict {monday: [{startTime,endTime,setpoint}], …} (lowercase day keys, minutes since
# midnight). All endpoints under the same system-control/v1 base.
#
# Key: (top_section, subsection, leaf_key) — identical to map_key() for indexed sections.
# Value: (endpoint_template, setpoint_required). {i} = index from path[1].
SCHEDULE_MAP: dict[tuple[str, str, str], tuple[str, bool]] = {
    # DHW circulation pump — VERIFIED (202 Accepted, 2026-07-17). No setpoint (pump).
    ("domesticHotWaterSettings", "configuration", "circulationPumpTimePeriods"): (
        "domestic-hot-water/{i}/circulation-pump-time-periods",
        False,
    ),
    # Zone heating periods — endpoint from the system-control list; setpointRequiredPerSlot=true
    # (5–30 °C, step 0.5). Body confirmed via no-op probe.
    ("zoneSettings", "heating", "timePeriods"): (
        "zones/{i}/heating-time-periods",
        True,
    ),
    # DHW charge periods (circuitTimePeriods) — VERIFIED via no-op probe (202 Accepted,
    # 2026-07-17). The other candidates (time-periods, loading-time-periods,
    # dhw-time-periods) returned 404. No setpoint (DHW charge).
    ("domesticHotWaterSettings", "configuration", "circuitTimePeriods"): (
        "domestic-hot-water/{i}/circuit-time-periods",
        False,
    ),
}

_DAY_ALIASES: dict[str, str] = {
    "monday": "monday",
    "mon": "monday",
    "mo": "monday",
    "tuesday": "tuesday",
    "tue": "tuesday",
    "di": "tuesday",
    "tu": "tuesday",
    "wednesday": "wednesday",
    "wed": "wednesday",
    "mi": "wednesday",
    "we": "wednesday",
    "thursday": "thursday",
    "thu": "thursday",
    "do": "thursday",
    "th": "thursday",
    "friday": "friday",
    "fri": "friday",
    "fr": "friday",
    "saturday": "saturday",
    "sat": "saturday",
    "sa": "saturday",
    "sunday": "sunday",
    "sun": "sunday",
    "so": "sunday",
    "su": "sunday",
}


def schedule_spec(path: list[str]) -> tuple[str | None, bool] | None:
    """(endpoint_template, setpoint_required) for a schedule point, or None."""
    key = map_key(path)
    return SCHEDULE_MAP.get(key) if key else None


def build_schedule_url(path: list[str], system_id: str) -> str | None:
    spec = schedule_spec(path)
    if not spec or not spec[0]:
        return None
    endpoint_template, _ = spec
    index = path[1] if len(path) >= 2 else ""
    return f"{_base_url(system_id)}/{endpoint_template.format(i=index)}"


def _to_minutes(value) -> int:
    """'HH:MM' or minutes (int/float/str) → minutes since midnight (0–1440)."""
    if isinstance(value, bool):  # bool is an int subclass — never meant here
        raise ValueError(f"Invalid time: {value!r}")
    if isinstance(value, (int, float)):
        minutes = int(value)
    elif isinstance(value, str) and ":" in value:
        hh, _, mm = value.partition(":")
        minutes = int(hh) * 60 + int(mm)
    elif isinstance(value, str):
        minutes = int(value)
    else:
        raise ValueError(f"Invalid time: {value!r}")
    if not 0 <= minutes <= 1440:
        raise ValueError(f"Time outside 0–1440 min: {value!r}")
    return minutes


def _slot_value(slot: dict, *keys):
    for k in keys:
        if k in slot and slot[k] is not None:
            return slot[k]
    return None


def build_schedule_body(schedule: dict, setpoint_required: bool) -> dict:
    """User schedule → API body {monday: [{startTime,endTime,setpoint}], …}.

    Day keys are tolerant (English/German, long/short) → lowercase English. Times as
    'HH:MM' or minutes. setpoint: required per slot when setpoint_required (clamped 5–30),
    otherwise always null (pump / DHW charge)."""
    if not isinstance(schedule, dict):
        raise ValueError("schedule must be a dict {day: [slots]}")
    body: dict[str, list[dict]] = {}
    for raw_day, slots in schedule.items():
        day = _DAY_ALIASES.get(str(raw_day).strip().lower())
        if not day:
            raise ValueError(f"Unknown weekday: {raw_day!r}")
        out_slots: list[dict] = []
        for slot in slots or []:
            start = _slot_value(slot, "startTime", "start_time", "start")
            end = _slot_value(slot, "endTime", "end_time", "end")
            if start is None or end is None:
                raise ValueError(f"Slot needs start and end time: {slot!r} ({day})")
            entry = {"startTime": _to_minutes(start), "endTime": _to_minutes(end)}
            if setpoint_required:
                sp = _slot_value(slot, "setpoint", "temperature")
                if sp is None:
                    raise ValueError(
                        f"Zone heating periods need a setpoint per slot: {slot!r} ({day})"
                    )
                entry["setpoint"] = max(5.0, min(30.0, float(sp)))
            else:
                entry["setpoint"] = None
            out_slots.append(entry)
        body[day] = out_slots
    return body


async def patch_schedule(api, path: list[str], system_id: str, schedule: dict) -> None:
    """PATCH a full weekly schedule to the matching endpoint. Raises on HTTP error."""
    spec = schedule_spec(path)
    if not spec:
        raise ValueError(f"No schedule endpoint for {path}")
    endpoint_template, setpoint_required = spec
    url = build_schedule_url(path, system_id)
    if not endpoint_template or not url:
        raise ValueError(
            f"Schedule endpoint for {map_key(path)} not confirmed yet — not writable"
        )
    body = build_schedule_body(schedule, setpoint_required)
    _LOGGER.debug("scf PATCH schedule %s %s", url, body)
    async with api.aiohttp_session.patch(
        url, json=body, headers=api.get_authorized_headers()
    ) as resp:
        resp.raise_for_status()
