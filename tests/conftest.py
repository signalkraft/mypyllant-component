from unittest.mock import Mock
from uuid import uuid4

from pydantic_factories import ModelFactory
import pytest

from myPyllant.models import Circuit, DomesticHotWater, System, SystemDevice, Zone

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
    zone = ZoneFactory.build(humidity=61.0, current_room_temperature=19.0).dict()
    del zone["system_id"]

    circuit = CircuitFactory.build(
        heating_curve=0.8,
        min_flow_temperature_setpoint=35.0,
        current_circuit_flow_temperature=50.0,
    ).dict()
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
            SystemDevice(
                **{
                    "device_id": "deviceId3",
                    "serial_number": "serialNumber3",
                    "article_number": "0020260951",
                    "name": "sensoHOME",
                    "type": "CONTROL",
                    "system_id": system_id,
                    "diagnostic_trouble_codes": [],
                }
            ),
            SystemDevice(
                **{
                    "device_id": "deviceId1",
                    "serial_number": "serialNumber1",
                    "article_number": "articleNumber1",
                    "name": "ecoTEC",
                    "type": "HEAT_GENERATOR",
                    "operational_data": {
                        "water_pressure": {
                            "value": 1.2,
                            "unit": "BAR",
                            "step_size": 0.1,
                        }
                    },
                    "system_id": system_id,
                    "diagnostic_trouble_codes": [],
                    "properties": ["EMF"],
                }
            ),
        ],
    }
    coordinator.data = [SystemFactory.build(id=system_id, **system_data)]
    yield coordinator


@pytest.fixture
def hourly_data_coordinator_mock(hass):
    """Fixture to mock the hourly data coordinator."""
    return Mock(data=hourly_data_coordinator_gas.data, hass=hass)
