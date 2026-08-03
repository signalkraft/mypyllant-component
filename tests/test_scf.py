"""
Tests for the scf/iQconnect branch (self-describing state tree → HA entities).

These exercise the pure logic that a reviewer cannot reproduce on real hardware:
- walk_state() leaf classification (incl. the "writable but unmapped → stays sensor" rule),
- the write mapping (endpoint + body key, circuits plural),
- weekly-schedule body building (day aliases, HH:MM vs minutes, setpoint clamp/null).

scf_state_sample.json is a real, anonymized capture from a geoCOMPACT VWS 52/8.1 iQ
(VR_NEEXT), produced by myPyllant's tests/generate_test_data.py - the same payload as the
tests/data/scf fixture in the library. It replaced a hand-written stub whose tree was a level
flatter than the device's (systemParameters really nests state/configuration/properties).
"""

import json
from pathlib import Path

import pytest

from myPyllant.api import MyPyllantAPI
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import load_test_data

from custom_components.mypyllant.scf import walk_state
from custom_components.mypyllant.scf_write import (
    build_schedule_body,
    build_url,
    map_key,
    patch_schedule,
    patch_value,
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
    assert platforms["systemParameters/state/systemFlowTemperature"] == "sensor"
    assert platforms["systemParameters/state/waterPressure"] == "sensor"
    # bool value with no write mapping → binary_sensor
    assert (
        platforms["systemParameters/state/isFrostProtectionActive"] == "binary_sensor"
    )
    # writable + verified write mapping → controls
    assert platforms["zoneSettings/1/general/operationMode"] == "select"
    assert platforms["zoneSettings/1/heating/manualModeTemperatureSetpoint"] == "number"
    assert platforms["circuitSettings/1/configuration/heatingCurve"] == "number"
    assert (
        platforms["domesticHotWaterSettings/1/configuration/operationMode"] == "select"
    )
    # TIME_PERIODS → schedule sensor
    assert platforms["zoneSettings/1/heating/timePeriods"] == "sensor"
    assert (
        platforms["domesticHotWaterSettings/1/configuration/circulationPumpTimePeriods"]
        == "sensor"
    )


def test_writable_without_mapping_stays_a_sensor():
    points = _by_path(walk_state(SYSTEM_ID, STATE))
    # heatingFlowTemperatureMinimumSetpoint is writable in metadata but has no verified
    # write endpoint → it must NOT become a control (no entity writing into the void).
    p = points["circuitSettings/1/configuration/heatingFlowTemperatureMinimumSetpoint"]
    assert p.writable is True
    assert p.has_write is False
    assert p.platform() == "sensor"


def test_null_values_are_skipped():
    points = _by_path(walk_state(SYSTEM_ID, STATE))
    # The device reports a lot of leaves it has no sensor for (114 in this capture) as
    # value: null - they must not turn into permanently-unknown entities.
    assert "systemParameters/state/heatingCylinderTopTemperature" not in points
    assert "systemParameters/state/energyManagerState" not in points


def test_capture_yields_the_expected_shape():
    """Locks in what this real capture produces, so a regression in walk_state shows up as
    a count change rather than silently dropping entities."""
    points = walk_state(SYSTEM_ID, STATE)
    assert len(points) == 95
    assert {p.section for p in points} == {
        "System",
        "Zone 1",
        "Circuit 1",
        "Domestic Hot Water 1",
    }
    controls = sorted("/".join(p.path) for p in points if p.has_write)
    assert controls == [
        "circuitSettings/1/configuration/heatingCurve",
        "domesticHotWaterSettings/1/configuration/cylinderTemperatureSetpoint",
        "domesticHotWaterSettings/1/configuration/operationMode",
        "zoneSettings/1/general/operationMode",
        "zoneSettings/1/heating/manualModeTemperatureSetpoint",
    ]
    assert len([p for p in points if p.is_schedule]) == 3


def test_write_mapping_and_url():
    path = ["circuitSettings", "1", "configuration", "heatingCurve"]
    assert map_key(path) == ("circuitSettings", "configuration", "heatingCurve")
    endpoint, body_key = write_spec(path)
    assert endpoint == "circuits/{i}/heating-curve"  # plural!
    assert body_key == "heatingCurve"
    url = build_url(path, SYSTEM_ID)
    assert url.endswith(f"/systems/{SYSTEM_ID}/circuits/1/heating-curve")


def test_write_mapping_unmapped_returns_none():
    assert (
        write_spec(
            ["circuitSettings", "1", "configuration", "minFlowTemperatureSetpoint"]
        )
        is None
    )


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
        build_schedule_body(
            {"monday": [{"start": "05:00", "end": "06:00"}]}, setpoint_required=True
        )


# --- Integration against the library's captured fixture ----------------------
# These need a myPyllant that ships tests/data/scf with a captured scf_state.json and
# whose aioresponses harness replays system-control/v1 URLs (signalkraft/myPyllant#161
# plus the follow-up "Make scf state tree capturable and replayable in tests"). They skip
# themselves on older releases, so the suite stays green until that lands on PyPI.

SCF_FIXTURE_DIR = DATA_DIR / "scf"
requires_scf_fixture = pytest.mark.skipif(
    not any(SCF_FIXTURE_DIR.glob("*/scf_state.json")),
    reason=(
        "Needs a myPyllant release with the captured tests/data/scf fixture and "
        "system-control/v1 replay in the test harness"
    ),
)


@requires_scf_fixture
async def test_coordinator_derives_scf_system_from_state(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    """End to end through the coordinator: an scf home yields no aggregate System, but a
    fully populated ScfSystem read from system-control/v1/.../state."""
    test_data = load_test_data(SCF_FIXTURE_DIR)
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert system_coordinator_mock.data == []
        assert len(system_coordinator_mock.scf_systems) == 1
        scf_system = system_coordinator_mock.scf_systems[0]
        assert len(scf_system.points) == 95
        assert len([p for p in scf_system.points if p.has_write]) == 5
        await mocked_api.aiohttp_session.close()


@requires_scf_fixture
async def test_scf_writes_reach_the_verified_endpoints(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI
):
    """The five verified write paths and the three schedule endpoints must PATCH cleanly
    (the harness answers 202 for exactly those URLs)."""
    test_data = load_test_data(SCF_FIXTURE_DIR)
    with mypyllant_aioresponses(test_data) as _:
        await patch_value(
            mocked_api,
            ["circuitSettings", "1", "configuration", "heatingCurve"],
            SYSTEM_ID,
            1.2,
        )
        await patch_schedule(
            mocked_api,
            ["zoneSettings", "1", "heating", "timePeriods"],
            SYSTEM_ID,
            {"monday": [{"start": "05:30", "end": "06:00", "setpoint": 21}]},
        )
        await mocked_api.aiohttp_session.close()
