from unittest.mock import Mock
from uuid import uuid4

from myPyllant.models import Circuit, DomesticHotWater, System, Zone
from pydantic_factories import ModelFactory
import pytest

from tests.data import hourly_data_coordinator_gas


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


class SystemFactory(ModelFactory):
    __model__ = System


class ZoneFactory(ModelFactory):
    __model__ = Zone


class CircuitFactory(ModelFactory):
    __model__ = Circuit


class DomesticHotWaterFactory(ModelFactory):
    __model__ = DomesticHotWater


@pytest.fixture
def system_coordinator_mock(hass):
    """Fixture to mock the update data coordinator."""
    coordinator = Mock(data={}, hass=hass)
    system_id = str(uuid4())
    zone = ZoneFactory.build(humidity=61.0).dict()
    del zone["system_id"]

    circuit = CircuitFactory.build(heating_curve=0.8, min_flow_temperature_setpoint=35.0).dict()
    del circuit["system_id"]

    dhw = DomesticHotWaterFactory.build(current_dhw_tank_temperature=50).dict()
    del dhw["system_id"]

    system_data = {
        "system_control_state": {
            "control_state": {
                "general": {
                    "outdoor_temperature": 5.5,
                    "system_water_pressure": 1.7,
                    "system_mode": "IDLE",
                },
                "zones": [zone],
                "circuits": [circuit],
                "domestic_hot_water": [dhw],
            }
        },
        "devices": [
            {
                "deviceId": "123456",
                "serialNumber": "212213002026091401111111N8",
                "articleNumber": "0020260914",
                "name": "sensoCOMFORT",
                "type": "CONTROL",
                "systemId": system_id,
                "diagnosticTroubleCodes": [],
            },
            {
                "deviceId": "123457",
                "serialNumber": "21222700100211180001111111N0",
                "articleNumber": "0010021118",
                "name": "aroTHERM plus",
                "type": "HEAT_GENERATOR",
                "operationalData": {
                    "waterPressure": {"value": 1.3, "unit": "BAR", "stepSize": 0.1}
                },
                "systemId": system_id,
                "diagnosticTroubleCodes": [],
                "properties": ["EMF"],
            },
        ],
    }
    coordinator.data = [SystemFactory.build(id=system_id, **system_data)]
    yield coordinator


@pytest.fixture
def hourly_data_coordinator_mock(hass):
    """Fixture to mock the hourly data coordinator."""
    return Mock(data=hourly_data_coordinator_gas.data, hass=hass)
