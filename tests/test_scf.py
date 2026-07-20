"""
Tests for the scf/iQconnect branch (self-describing state tree → HA entities).

These exercise the pure logic that a reviewer cannot reproduce on real hardware:
- walk_state() leaf classification (incl. the "writable but unmapped → stays sensor" rule),
- the write mapping (endpoint + body key, circuits plural),
- weekly-schedule body building (day aliases, HH:MM vs minutes, setpoint clamp/null).
"""

import json
from pathlib import Path

import pytest

from custom_components.mypyllant.scf import walk_state
from custom_components.mypyllant.scf_write import (
    build_schedule_body,
    build_url,
    map_key,
    write_spec,
)

SYSTEM_ID = "00000000-0000-0000-0000-000000000000"
STATE = json.loads((Path(__file__).parent / "scf_state_sample.json").read_text())


def _by_path(points):
    return {"/".join(p.path): p for p in points}


def test_walk_state_classifies_each_leaf():
    points = _by_path(walk_state(SYSTEM_ID, STATE))
    platforms = {path: p.platform() for path, p in points.items()}

    # read-only telemetry
    assert platforms["systemParameters/systemFlowTemperature"] == "sensor"
    assert platforms["systemParameters/systemWaterPressure"] == "sensor"
    # bool value with no write mapping → binary_sensor
    assert platforms["systemParameters/isFrostProtectionActive"] == "binary_sensor"
    # writable + verified write mapping → controls
    assert platforms["zoneSettings/1/general/operationMode"] == "select"
    assert platforms["zoneSettings/1/heating/manualModeTemperatureSetpoint"] == "number"
    assert platforms["circuitSettings/1/configuration/heatingCurve"] == "number"
    assert platforms["domesticHotWaterSettings/1/configuration/operationMode"] == "select"
    # TIME_PERIODS → schedule sensor
    assert platforms["zoneSettings/1/heating/timePeriods"] == "sensor"
    assert (
        platforms["domesticHotWaterSettings/1/configuration/circulationPumpTimePeriods"]
        == "sensor"
    )


def test_writable_without_mapping_stays_a_sensor():
    points = _by_path(walk_state(SYSTEM_ID, STATE))
    # minFlowTemperatureSetpoint is writable in metadata but has no verified write
    # endpoint → it must NOT become a control (no entity writing into the void).
    p = points["circuitSettings/1/configuration/minFlowTemperatureSetpoint"]
    assert p.writable is True
    assert p.has_write is False
    assert p.platform() == "sensor"


def test_null_values_are_skipped():
    points = _by_path(walk_state(SYSTEM_ID, STATE))
    assert "systemParameters/currentRoomTemperature" not in points


def test_write_mapping_and_url():
    path = ["circuitSettings", "1", "configuration", "heatingCurve"]
    assert map_key(path) == ("circuitSettings", "configuration", "heatingCurve")
    endpoint, body_key = write_spec(path)
    assert endpoint == "circuits/{i}/heating-curve"  # plural!
    assert body_key == "heatingCurve"
    url = build_url(path, SYSTEM_ID)
    assert url.endswith(f"/systems/{SYSTEM_ID}/circuits/1/heating-curve")


def test_write_mapping_unmapped_returns_none():
    assert write_spec(["circuitSettings", "1", "configuration", "minFlowTemperatureSetpoint"]) is None


def test_schedule_body_zone_heating_needs_setpoint_and_clamps():
    schedule = {
        "Mo": [{"start": "05:30", "end": "06:00", "setpoint": 21}],
        "tuesday": [{"start": 1050, "end": 1080, "setpoint": 40}],  # clamps to 30
    }
    body = build_schedule_body(schedule, setpoint_required=True)
    assert body["monday"] == [{"startTime": 330, "endTime": 360, "setpoint": 21.0}]
    assert body["tuesday"] == [{"startTime": 1050, "endTime": 1080, "setpoint": 30.0}]


def test_schedule_body_pump_forces_null_setpoint():
    schedule = {"monday": [{"start": "05:00", "end": "05:30", "setpoint": 21}]}
    body = build_schedule_body(schedule, setpoint_required=False)
    assert body["monday"][0]["setpoint"] is None


def test_schedule_body_rejects_bad_input():
    with pytest.raises(ValueError):
        build_schedule_body({"notaday": []}, setpoint_required=False)
    with pytest.raises(ValueError):
        build_schedule_body({"monday": [{"start": "05:00"}]}, setpoint_required=False)
    with pytest.raises(ValueError):
        build_schedule_body({"monday": [{"start": "05:00", "end": "06:00"}]}, setpoint_required=True)
