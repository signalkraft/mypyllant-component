"""scf branch (iQconnect / VR_NEEXT devices).

Why standalone: myPyllant builds `System` objects from the aggregate endpoint
`/{controlIdentifier}/v1/systems/{id}` — which does NOT exist for `scf` (404). scf devices
instead expose their state under
    GET system-control/v1/systems/{id}/state
in a completely different but **self-describing** format:
    { "value": <x>, "metadata": {writable, type, minimum, maximum, stepSize, allowedValues}, ... }

This self-description is the trick: instead of maintaining 40 entities by hand, `walk_state()`
walks the tree and derives each entity's type + bounds directly from `metadata`. New fields from
a later rollout therefore appear automatically. Verified against the live device state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from myPyllant.const import SYSTEM_CONTROL_API_URL_BASE

from custom_components.mypyllant.scf_write import write_spec

_LOGGER = logging.getLogger(__name__)


async def fetch_scf_state(api, system_id: str) -> dict:
    """Fetch the raw state of an scf system."""
    url = f"{SYSTEM_CONTROL_API_URL_BASE}/systems/{system_id}/state"
    async with api.aiohttp_session.get(
        url, headers=api.get_authorized_headers()
    ) as resp:
        resp.raise_for_status()
        return await resp.json()


# Sections of the state tree → (display prefix, is-indexed)
# systemParameters is a single object; zone/circuit/dhw are grouped by index.
_SECTIONS = {
    "systemParameters": ("System", False),
    "zoneSettings": ("Zone", True),
    "circuitSettings": ("Circuit", True),
    "domesticHotWaterSettings": ("Domestic Hot Water", True),
}


@dataclass
class ScfPoint:
    """A leaf from the state tree, classified for Home Assistant."""

    system_id: str
    section: str  # e.g. "System", "Zone 1", "Domestic Hot Water 1"
    key: str  # leaf name, e.g. "systemFlowTemperature"
    unique_suffix: str  # stable ID derived from the path
    value: Any
    metadata: dict | None
    path: list[str]  # full path for later write mapping

    @property
    def writable(self) -> bool:
        return bool(
            self.metadata
            and self.metadata.get("writable")
            and self.metadata.get("enabled")
        )

    @property
    def mtype(self) -> str | None:
        return self.metadata.get("type") if self.metadata else None

    @property
    def is_schedule(self) -> bool:
        """Weekly schedule (TIME_PERIODS): value is a dict {DAY: [{startTime,endTime,setpoint}]}."""
        return self.mtype == "TIME_PERIODS" and isinstance(self.value, dict)

    @property
    def has_write(self) -> bool:
        """Only fields with a verified write mapping are controllable."""
        return self.writable and write_spec(self.path) is not None

    def platform(self) -> str:
        """Derive the HA platform from value + metadata + write mapping.

        Without a confirmed write endpoint a field stays a (read-only) sensor — even if the
        API marks it writable. That way nothing disappears and no controls are created that
        would write into the void."""
        if self.is_schedule:
            return "sensor"  # weekly schedule as a read-only sensor (status + per-day attributes)
        if self.has_write:
            t = self.mtype
            if t == "BOOL":
                return "switch"
            if t == "ENUM":
                return "select"
            if t in ("FLOAT", "LONG"):
                return "number"
        if isinstance(self.value, bool):
            return "binary_sensor"
        return "sensor"


def _walk(node: Any, path: list[str], sid: str, out: list[ScfPoint]) -> None:
    """Recursive: a leaf is a dict with the keys value/metadata/lastUpdated."""
    if isinstance(node, dict) and "value" in node and "metadata" in node:
        section = _section_label(path)
        key = path[-1]
        _add_point(sid, section, key, path, node, out)
        return
    if isinstance(node, dict):
        for k, v in node.items():
            _walk(v, path + [k], sid, out)


def _section_label(path: list[str]) -> str:
    top = path[0] if path else ""
    label, indexed = _SECTIONS.get(top, (top, False))
    if indexed and len(path) >= 2:
        return f"{label} {path[1]}"
    return label


def _add_point(sid, section, key, path, node, out) -> None:
    value = node.get("value")
    if value is None:
        return  # device does not provide this field → skip, do not crash
    metadata = node.get("metadata")
    mtype = metadata.get("type") if metadata else None
    # Let weekly schedules (TIME_PERIODS) through — rendered as a schedule sensor.
    # Other complex values (objects/lists) are not entities → skip.
    if isinstance(value, (dict, list)) and mtype != "TIME_PERIODS":
        return
    out.append(
        ScfPoint(
            system_id=sid,
            section=section,
            key=key,
            unique_suffix="_".join(path),
            value=value,
            metadata=node.get("metadata"),
            path=path,
        )
    )


def walk_state(system_id: str, state: dict) -> list[ScfPoint]:
    """Translate the full state tree into a flat list of HA-ready points."""
    data = (state or {}).get("data", {})
    out: list[ScfPoint] = []
    for top in _SECTIONS:
        if top in data:
            _walk(data[top], [top], system_id, out)
    _LOGGER.debug("scf %s: derived %d points from state", system_id, len(out))
    return out


@dataclass
class ScfSystem:
    """Parsed state of an scf system as consumed by the entities."""

    system_id: str
    home_name: str
    nomenclature: str
    points: list[ScfPoint] = field(default_factory=list)

    def by_platform(self, platform: str) -> list[ScfPoint]:
        return [p for p in self.points if p.platform() == platform]
