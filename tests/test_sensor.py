import pytest as pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.recorder.statistics import StatisticMeanType
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS

from myPyllant.api import MyPyllantAPI
from myPyllant.models import DeviceData, DeviceDataBucket
from myPyllant.enums import CircuitState
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import list_test_data, load_test_data

from custom_components.mypyllant.sensor import (
    CircuitFlowTemperatureSensor,
    CircuitHeatingCurveSensor,
    CircuitMinFlowTemperatureSetpointSensor,
    CircuitStateSensor,
    DataSensor,
    DomesticHotWaterCurrentSpecialFunctionSensor,
    DomesticHotWaterOperationModeSensor,
    DomesticHotWaterSetPointSensor,
    DomesticHotWaterTankTemperatureSensor,
    HomeEntity,
    SystemOutdoorTemperatureSensor,
    ZoneCurrentRoomTemperatureSensor,
    ZoneCurrentSpecialFunctionSensor,
    ZoneDesiredRoomTemperatureSetpointSensor,
    ZoneHeatingOperatingModeSensor,
    ZoneHumiditySensor,
    SystemDeviceOnOffCyclesSensor,
    SystemDeviceOperationTimeSensor,
    create_system_sensors,
    SystemTopDHWTemperatureSensor,
    SystemBottomDHWTemperatureSensor,
    SystemTopCHTemperatureSensor,
    SystemDeviceCurrentPowerSensor,
)
from custom_components.mypyllant.const import DOMAIN
from tests.utils import get_config_entry


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=True))
async def test_create_system_sensors(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    hass.data[DATA_COMPONENTS] = {}
    hass.data[DATA_INTEGRATIONS] = {}
    hass.data[DATA_REGISTRY] = EntityRegistry(hass)
    with mypyllant_aioresponses(test_data) as _:
        config_entry = get_config_entry()
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        hass.data[DOMAIN] = {
            config_entry.entry_id: {"system_coordinator": system_coordinator_mock}
        }
        sensors = await create_system_sensors(hass, config_entry)
        assert len(sensors) > 0

        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=True))
async def test_system_sensors(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        if "outdoorTemperature" in str(test_data):
            assert isinstance(
                SystemOutdoorTemperatureSensor(0, system_coordinator_mock).native_value,
                float,
            )
        # TODO: No water pressure in no_cooling.yaml
        # assert isinstance(
        #    SystemWaterPressureSensor(0, system_coordinator_mock).native_value, float
        # )

        home = HomeEntity(0, system_coordinator_mock)
        assert isinstance(home.device_info, dict)
        assert (
            home.extra_state_attributes
            and "controller_type" in home.extra_state_attributes
        )

        await mocked_api.aiohttp_session.close()


async def test_zone_sensors(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
):
    test_data = load_test_data(DATA_DIR / "heatpump_cooling")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        if "humidity" in str(test_data):
            assert isinstance(
                ZoneHumiditySensor(0, 0, system_coordinator_mock).native_value, float
            )
        if "currentTemperature" in str(test_data):
            assert isinstance(
                ZoneCurrentRoomTemperatureSensor(
                    0, 0, system_coordinator_mock
                ).native_value,
                float,
            )
        assert isinstance(
            ZoneDesiredRoomTemperatureSetpointSensor(
                0, 0, system_coordinator_mock
            ).native_value,
            float | int,
        )
        assert isinstance(
            ZoneCurrentSpecialFunctionSensor(
                0, 0, system_coordinator_mock
            ).native_value,
            str,
        )
        assert isinstance(
            ZoneHeatingOperatingModeSensor(0, 0, system_coordinator_mock).native_value,
            str,
        )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=True))
async def test_circuit_sensors(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        circuit_state = CircuitStateSensor(0, 0, system_coordinator_mock)
        assert isinstance(circuit_state.native_value, CircuitState)
        assert isinstance(circuit_state.extra_state_attributes, dict)
        if "room_temperature_control_mode" in test_data:
            assert (
                "room_temperature_control_mode" in circuit_state.extra_state_attributes
            )
        # Regression test for #422 / #440: heating_circuit_flow_setpoint was
        # surfaced via extra_fields before upstream promoted it to a typed
        # Circuit field. CircuitStateSensor must continue to expose it as an
        # attribute so existing automations/templates do not break silently.
        # Guarded against fixtures that lack the field (e.g. no_system) where
        # the assertion would otherwise be vacuous (None == None).
        if "heatingCircuitFlowSetpoint" in str(test_data):
            assert (
                "heating_circuit_flow_setpoint" in circuit_state.extra_state_attributes
            )
            assert (
                circuit_state.extra_state_attributes["heating_circuit_flow_setpoint"]
                == circuit_state.circuit.heating_circuit_flow_setpoint
            )
        assert isinstance(
            CircuitFlowTemperatureSensor(0, 0, system_coordinator_mock).native_value,
            (int, float, complex),
        )
        if "heatingCurve" in str(test_data):
            assert isinstance(
                CircuitHeatingCurveSensor(0, 0, system_coordinator_mock).native_value,
                (int, float, complex),
            )
        if "minFlowTemperatureSetpoint" in str(test_data):
            assert isinstance(
                CircuitMinFlowTemperatureSetpointSensor(
                    0, 0, system_coordinator_mock
                ).native_value,
                (int, float, complex),
            )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize(
    "test_data", list_test_data(only_with_systems=True, only_with_dhw=True)
)
async def test_domestic_hot_water_sensor(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert isinstance(
            DomesticHotWaterOperationModeSensor(
                0, 0, system_coordinator_mock
            ).native_value,
            str,
        )
        assert isinstance(
            DomesticHotWaterSetPointSensor(0, 0, system_coordinator_mock).native_value,
            (int, float, complex),
        )
        assert isinstance(
            DomesticHotWaterCurrentSpecialFunctionSensor(
                0, 0, system_coordinator_mock
            ).native_value,
            str,
        )
        if "currentDhwTankTemperature" in str(test_data):
            assert isinstance(
                DomesticHotWaterTankTemperatureSensor(
                    0, 0, system_coordinator_mock
                ).native_value,
                float,
            )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=True))
async def test_data_sensor(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    daily_data_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = daily_data_coordinator_mock.hass_data["system_coordinator"]
        system_coordinator.data = await system_coordinator._async_update_data()
        daily_data_coordinator_mock.data = (
            await daily_data_coordinator_mock._async_update_data()
        )
        system_id = next(iter(daily_data_coordinator_mock.data), None)
        if system_id is None or not daily_data_coordinator_mock.data[system_id]:
            await mocked_api.aiohttp_session.close()
            pytest.skip(f"No devices in system {system_id}, skipping data sensor tests")
        data_sensor = DataSensor(system_id, 0, 0, daily_data_coordinator_mock)
        assert isinstance(
            data_sensor.device_data,
            DeviceData,
        )
        assert isinstance(
            data_sensor.native_value,
            (int, float, complex),
        )
        assert isinstance(
            data_sensor.name,
            str,
        )
        assert data_sensor.last_reset is None
        await mocked_api.aiohttp_session.close()


async def test_device_sensor(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
):
    test_data = load_test_data(DATA_DIR / "vrc700_mpc_rts.yaml")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert isinstance(
            SystemDeviceOnOffCyclesSensor(0, 0, system_coordinator_mock).native_value,
            int,
        )
        assert isinstance(
            SystemDeviceOperationTimeSensor(0, 0, system_coordinator_mock).native_value,
            float,
        )
        assert isinstance(
            SystemDeviceCurrentPowerSensor(0, 0, system_coordinator_mock).native_value,
            int,
        )
        await mocked_api.aiohttp_session.close()


async def test_additional_system_sensors(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
):
    test_data = load_test_data(DATA_DIR / "two_systems")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert isinstance(
            SystemTopDHWTemperatureSensor(0, system_coordinator_mock).native_value,
            float,
        )
        assert isinstance(
            SystemBottomDHWTemperatureSensor(0, system_coordinator_mock).native_value,
            float,
        )
        assert isinstance(
            SystemTopCHTemperatureSensor(0, system_coordinator_mock).native_value,
            float,
        )
        await mocked_api.aiohttp_session.close()


# ---------------------------------------------------------------------------
# Helpers for _write_hourly_statistics tests
# ---------------------------------------------------------------------------

_MIDNIGHT = datetime(2026, 5, 27, 0, 0, tzinfo=timezone.utc)
_SYSTEM_ID = "test_system"


def _make_buckets(values):
    buckets = []
    for i, value in enumerate(values):
        start = _MIDNIGHT + timedelta(hours=i)
        buckets.append(
            DeviceDataBucket(
                start_date=start,
                end_date=start + timedelta(hours=1),
                value=value,
            )
        )
    return buckets


def _make_sensor(hass, buckets, data_from=_MIDNIGHT):
    device = MagicMock()
    device.device_uuid = "test-uuid"
    device.name_display = "Arotherm Plus"
    device.brand_name = "Vaillant"
    device.product_name_display = "aroTHERM plus"

    device_data = DeviceData(
        operation_mode="HEATING",
        energy_type="CONSUMED_ELECTRICAL_ENERGY",
        data_from=data_from,
        total_consumption=sum(v for v in (b.value for b in buckets) if v is not None),
        device=device,
        data=buckets,
    )
    coordinator = MagicMock()
    coordinator.data = {
        _SYSTEM_ID: {
            "devices_data": [[device_data]],
            "home_name": "Test Home",
        }
    }
    sensor = DataSensor(_SYSTEM_ID, 0, 0, coordinator)
    sensor.hass = hass
    return sensor


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_write_hourly_statistics_correct_data(hass):
    buckets = _make_buckets([100.0, 200.0, 300.0])
    sensor = _make_sensor(hass, buckets)

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor._write_hourly_statistics()

    mock_stats.assert_called_once()
    _, metadata, stats = mock_stats.call_args[0]
    stats = list(stats)

    assert metadata["statistic_id"].startswith(f"{DOMAIN}:")
    assert metadata["mean_type"] == StatisticMeanType.NONE
    assert metadata["has_sum"] is True
    assert metadata["unit_class"] == "energy"

    assert len(stats) == 3
    assert stats[0]["start"] == buckets[0].start_date
    # state is day-cumulative (mirrors octopus_energy), equal to sum when baseline is 0
    assert stats[0]["state"] == 100.0
    assert stats[0]["sum"] == 100.0
    assert stats[1]["state"] == 300.0
    assert stats[1]["sum"] == 300.0
    assert stats[2]["state"] == 600.0
    assert stats[2]["sum"] == 600.0


async def test_write_hourly_statistics_skips_none_values(hass):
    buckets = _make_buckets([100.0, None, 300.0])
    sensor = _make_sensor(hass, buckets)

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor._write_hourly_statistics()

    mock_stats.assert_called_once()
    _, _, stats = mock_stats.call_args[0]
    stats = list(stats)

    assert len(stats) == 2
    assert stats[0]["state"] == 100.0
    assert stats[0]["sum"] == 100.0
    assert stats[1]["state"] == 400.0  # day-cumulative: 100 + 300
    assert stats[1]["sum"] == 400.0


async def test_write_hourly_statistics_no_data(hass):
    sensor = _make_sensor(hass, [])

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor._write_hourly_statistics()

    mock_stats.assert_not_called()


async def test_write_hourly_statistics_no_device_data(hass):
    coordinator = MagicMock()
    coordinator.data = {
        _SYSTEM_ID: {
            "devices_data": [],
            "home_name": "Test Home",
        }
    }
    sensor = DataSensor(_SYSTEM_ID, 0, 0, coordinator)
    sensor.hass = hass

    with patch(
        "custom_components.mypyllant.sensor.async_add_external_statistics"
    ) as mock_stats:
        await sensor._write_hourly_statistics()

    mock_stats.assert_not_called()


async def test_async_added_to_hass_writes_statistics(hass):
    buckets = _make_buckets([100.0, 200.0, 300.0])
    sensor = _make_sensor(hass, buckets)

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
        patch(
            "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_added_to_hass",
            new_callable=AsyncMock,
        ),
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor.async_added_to_hass()

    mock_stats.assert_called_once()


async def test_write_hourly_statistics_carries_forward_previous_sum(hass):
    """Yesterday's final sum is the baseline so statistics are always monotonically
    increasing across day boundaries, preventing a negative delta at BST midnight."""
    buckets = _make_buckets([100.0, 200.0])
    sensor = _make_sensor(hass, buckets)
    stat_id = f"{DOMAIN}:{sensor.unique_id}".lower().replace("-", "_")

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(
            return_value={stat_id: [{"sum": 3804.0}]}
        )
        await sensor._write_hourly_statistics()

    mock_stats.assert_called_once()
    _, _, stats = mock_stats.call_args[0]
    stats = list(stats)

    assert stats[0]["sum"] == 3904.0  # 3804 baseline + 100
    assert stats[1]["sum"] == 4104.0  # 3804 baseline + 100 + 200
    assert (
        stats[0]["state"] == 100.0
    )  # day-cumulative resets daily, independent of baseline
    assert stats[1]["state"] == 300.0


async def test_write_hourly_statistics_without_data_from(hass):
    """The myVAILLANT API does not always return `from`. Statistics must still be written,
    with day_start derived from the first bucket's timestamp (mirrors octopus_energy)."""
    buckets = _make_buckets([100.0, 200.0])
    sensor = _make_sensor(hass, buckets, data_from=None)

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor._write_hourly_statistics()

    mock_stats.assert_called_once()
    _, _, stats = mock_stats.call_args[0]
    stats = list(stats)
    assert len(stats) == 2
    assert stats[0]["sum"] == 100.0
    assert stats[1]["sum"] == 300.0
    # last_reset derived from first bucket floored to midnight
    assert stats[0]["last_reset"] == _MIDNIGHT


async def test_async_added_to_hass_survives_statistics_failure(hass):
    """A failure writing statistics must not prevent the entity from loading."""
    buckets = _make_buckets([100.0, 200.0, 300.0])
    sensor = _make_sensor(hass, buckets)

    with (
        patch(
            "custom_components.mypyllant.sensor.DataSensor._write_hourly_statistics",
            new_callable=AsyncMock,
            side_effect=RuntimeError("recorder not ready"),
        ),
        patch(
            "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_added_to_hass",
            new_callable=AsyncMock,
        ),
    ):
        # Should not raise
        await sensor.async_added_to_hass()


async def test_write_hourly_statistics_resets_state_across_day_boundary(hass):
    """The coordinator fetches a 2-day window (yesterday + today). sum must stay
    monotonically increasing across the midnight boundary, while state and last_reset
    reset at the start of each day (mirrors octopus_energy's day-cumulative state)."""
    day1 = datetime(2026, 5, 27, 0, 0, tzinfo=timezone.utc)
    day2 = datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc)
    buckets = [
        DeviceDataBucket(
            start_date=day1 + timedelta(hours=22),
            end_date=day1 + timedelta(hours=23),
            value=100.0,
        ),
        DeviceDataBucket(
            start_date=day1 + timedelta(hours=23),
            end_date=day2,
            value=200.0,
        ),
        DeviceDataBucket(
            start_date=day2,
            end_date=day2 + timedelta(hours=1),
            value=300.0,
        ),
        DeviceDataBucket(
            start_date=day2 + timedelta(hours=1),
            end_date=day2 + timedelta(hours=2),
            value=400.0,
        ),
    ]
    sensor = _make_sensor(hass, buckets, data_from=day1)

    with (
        patch("custom_components.mypyllant.sensor.get_instance") as mock_recorder,
        patch(
            "custom_components.mypyllant.sensor.async_add_external_statistics"
        ) as mock_stats,
    ):
        mock_recorder.return_value.async_add_executor_job = AsyncMock(return_value={})
        await sensor._write_hourly_statistics()

    _, _, stats = mock_stats.call_args[0]
    stats = list(stats)
    assert len(stats) == 4
    # sum is cumulative across both days (monotonic)
    assert [s["sum"] for s in stats] == [100.0, 300.0, 600.0, 1000.0]
    # state resets at the day-2 boundary
    assert [s["state"] for s in stats] == [100.0, 300.0, 300.0, 700.0]
    # last_reset is the midnight of each bucket's own day
    assert stats[0]["last_reset"] == day1
    assert stats[1]["last_reset"] == day1
    assert stats[2]["last_reset"] == day2
    assert stats[3]["last_reset"] == day2
