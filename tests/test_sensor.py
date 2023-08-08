import datetime
from unittest import mock

import pytest as pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import CircuitState, DeviceData
from myPyllant.tests.test_api import list_test_data

from custom_components.mypyllant import DailyDataCoordinator, SystemCoordinator
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
    SystemOutdoorTemperatureSensor,
    SystemWaterPressureSensor,
    ZoneCurrentRoomTemperatureSensor,
    ZoneCurrentSpecialFunctionSensor,
    ZoneDesiredRoomTemperatureSetpointSensor,
    ZoneHeatingOperatingModeSensor,
    ZoneHumiditySensor,
)


@pytest.mark.parametrize("test_data", list_test_data())
async def test_system_sensors(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), datetime.timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        if "outdoorTemperature" in str(test_data):
            assert isinstance(
                SystemOutdoorTemperatureSensor(0, system_coordinator).native_value,
                float,
            )
        assert isinstance(
            SystemWaterPressureSensor(0, system_coordinator).native_value, float
        )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_zone_sensors(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), datetime.timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        if "humidity" in str(test_data):
            assert isinstance(
                ZoneHumiditySensor(0, 0, system_coordinator).native_value, float
            )
        if "currentTemperature" in str(test_data):
            assert isinstance(
                ZoneCurrentRoomTemperatureSensor(0, 0, system_coordinator).native_value,
                float,
            )
        assert isinstance(
            ZoneDesiredRoomTemperatureSetpointSensor(
                0, 0, system_coordinator
            ).native_value,
            float,
        )
        assert isinstance(
            ZoneCurrentSpecialFunctionSensor(0, 0, system_coordinator).native_value,
            str,
        )
        assert isinstance(
            ZoneHeatingOperatingModeSensor(0, 0, system_coordinator).native_value, str
        )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_circuit_sensors(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), datetime.timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        assert isinstance(
            CircuitStateSensor(0, 0, system_coordinator).native_value, CircuitState
        )
        assert isinstance(
            CircuitFlowTemperatureSensor(0, 0, system_coordinator).native_value, float
        )
        if "heatingCurve" in str(test_data):
            assert isinstance(
                CircuitHeatingCurveSensor(0, 0, system_coordinator).native_value, float
            )
        if "minFlowTemperatureSetpoint" in str(test_data):
            assert isinstance(
                CircuitMinFlowTemperatureSetpointSensor(
                    0, 0, system_coordinator
                ).native_value,
                float,
            )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_domestic_hot_water_sensor(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), datetime.timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        if not system_coordinator.data[0].domestic_hot_water:
            pytest.skip(
                f"No DHW in system {system_coordinator.data[0]}, skipping DHW sensors"
            )
        assert isinstance(
            DomesticHotWaterOperationModeSensor(0, 0, system_coordinator).native_value,
            str,
        )
        assert isinstance(
            DomesticHotWaterSetPointSensor(0, 0, system_coordinator).native_value,
            float,
        )
        assert isinstance(
            DomesticHotWaterCurrentSpecialFunctionSensor(
                0, 0, system_coordinator
            ).native_value,
            str,
        )
        if "currentDhwTankTemperature" in str(test_data):
            assert isinstance(
                DomesticHotWaterTankTemperatureSensor(
                    0, 0, system_coordinator
                ).native_value,
                float,
            )
        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_data_sensor(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        daily_data_coordinator = DailyDataCoordinator(
            hass, mocked_api, mock.Mock(), datetime.timedelta(seconds=10)
        )
        daily_data_coordinator.data = await daily_data_coordinator._async_update_data()
        system_id = list(daily_data_coordinator.data.keys())[0]
        if not daily_data_coordinator.data[system_id]:
            pytest.skip(f"No devices in system {system_id}, skipping data sensor tests")
        data_sensor = DataSensor(system_id, 0, daily_data_coordinator)
        assert isinstance(
            data_sensor.device_data,
            DeviceData,
        )
        assert isinstance(
            data_sensor.native_value,
            float,
        )
        assert isinstance(
            data_sensor.name,
            str,
        )
        assert data_sensor.last_reset is None
        await mocked_api.aiohttp_session.close()
