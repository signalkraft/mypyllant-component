import pytest as pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import CircuitState, DeviceData
from myPyllant.tests.utils import list_test_data

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
    SystemWaterPressureSensor,
    ZoneCurrentRoomTemperatureSensor,
    ZoneCurrentSpecialFunctionSensor,
    ZoneDesiredRoomTemperatureSetpointSensor,
    ZoneHeatingOperatingModeSensor,
    ZoneHumiditySensor,
)


@pytest.mark.parametrize("test_data", list_test_data())
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
        assert isinstance(
            SystemWaterPressureSensor(0, system_coordinator_mock).native_value, float
        )

        home = HomeEntity(0, system_coordinator_mock)
        assert isinstance(home.device_info, dict)
        assert (
            home.extra_state_attributes
            and "controller_type" in home.extra_state_attributes
        )

        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_zone_sensors(
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
            float,
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


@pytest.mark.parametrize("test_data", list_test_data())
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


@pytest.mark.parametrize("test_data", list_test_data())
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
        if not system_coordinator_mock.data[0].domestic_hot_water:
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No DHW in system {system_coordinator_mock.data[0]}, skipping DHW sensors"
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


@pytest.mark.parametrize("test_data", list_test_data())
async def test_data_sensor(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    device_data_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        device_data_coordinator_mock.data = (
            await device_data_coordinator_mock._async_update_data()
        )
        for index, data in enumerate(device_data_coordinator_mock.data):
            if len(data) == 0:
                await mocked_api.aiohttp_session.close()
                pytest.skip(f"No devices in system {index}, skipping data sensor tests")

            data_sensor = DataSensor(index, 0, 0, device_data_coordinator_mock)
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
