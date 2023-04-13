import datetime

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
    SystemModeSensor,
    SystemOutdoorTemperatureSensor,
    SystemWaterPressureSensor,
    ZoneCurrentRoomTemperatureSensor,
    ZoneCurrentSpecialFunctionSensor,
    ZoneDesiredRoomTemperatureSetpointSensor,
    ZoneHeatingOperatingModeSensor,
    ZoneHumiditySensor,
)
from myPyllant.models import CircuitState


async def test_system_sensors(hass, system_coordinator_mock):
    assert isinstance(
        SystemOutdoorTemperatureSensor(0, system_coordinator_mock).native_value, float
    )
    assert isinstance(
        SystemWaterPressureSensor(0, system_coordinator_mock).native_value, float
    )
    assert isinstance(SystemModeSensor(0, system_coordinator_mock).native_value, str)


async def test_zone_sensors(hass, system_coordinator_mock):
    assert isinstance(
        ZoneHumiditySensor(0, 0, system_coordinator_mock).native_value, float
    )
    assert isinstance(
        ZoneCurrentRoomTemperatureSensor(0, 0, system_coordinator_mock).native_value,
        float,
    )
    assert isinstance(
        ZoneDesiredRoomTemperatureSetpointSensor(
            0, 0, system_coordinator_mock
        ).native_value,
        float,
    )
    assert isinstance(
        ZoneCurrentSpecialFunctionSensor(0, 0, system_coordinator_mock).native_value,
        str,
    )
    assert isinstance(
        ZoneHeatingOperatingModeSensor(0, 0, system_coordinator_mock).native_value, str
    )


async def test_circuit_sensors(hass, system_coordinator_mock):
    assert isinstance(
        CircuitStateSensor(0, 0, system_coordinator_mock).native_value, CircuitState
    )
    assert isinstance(
        CircuitFlowTemperatureSensor(0, 0, system_coordinator_mock).native_value, float
    )
    assert isinstance(
        CircuitHeatingCurveSensor(0, 0, system_coordinator_mock).native_value, float
    )
    assert isinstance(
        CircuitMinFlowTemperatureSetpointSensor(
            0, 0, system_coordinator_mock
        ).native_value,
        float,
    )


async def test_domestic_hot_water_sensor(hass, system_coordinator_mock):
    assert isinstance(
        DomesticHotWaterOperationModeSensor(0, 0, system_coordinator_mock).native_value,
        str,
    )
    assert isinstance(
        DomesticHotWaterSetPointSensor(0, 0, system_coordinator_mock).native_value,
        float,
    )
    assert isinstance(
        DomesticHotWaterCurrentSpecialFunctionSensor(
            0, 0, system_coordinator_mock
        ).native_value,
        str,
    )
    assert isinstance(
        DomesticHotWaterTankTemperatureSensor(
            0, 0, system_coordinator_mock
        ).native_value,
        float,
    )


async def test_data_sensor(hass, hourly_data_coordinator_mock):
    assert isinstance(
        DataSensor(0, 3, hourly_data_coordinator_mock).native_value,
        float,
    )
    assert (
        DataSensor(0, 3, hourly_data_coordinator_mock).name
        == "ecoTEC Consumed Primary Energy Heating"
    )
    assert isinstance(
        DataSensor(0, 3, hourly_data_coordinator_mock).last_reset, datetime.datetime
    )
