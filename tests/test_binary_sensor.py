import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import System
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.binary_sensor import (
    CircuitIsCoolingAllowed,
    ControlError,
    ControlOnline,
)
from custom_components.mypyllant.entities.circuit import CircuitFlowTemperatureSensor
from custom_components.mypyllant.entities.system import SystemOutdoorTemperatureSensor


@pytest.mark.parametrize("test_data", list_test_data())
async def test_system_binary_sensors(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        system = SystemOutdoorTemperatureSensor(0, system_coordinator_mock)
        assert isinstance(system.device_info, dict)

        circuit = CircuitFlowTemperatureSensor(0, 0, system_coordinator_mock)
        assert isinstance(circuit.device_info, dict)
        assert isinstance(circuit.system, System)

        assert ControlError(0, system_coordinator_mock).is_on is False
        assert isinstance(ControlError(0, system_coordinator_mock).name, str)
        assert ControlOnline(0, system_coordinator_mock).is_on is True
        assert isinstance(ControlOnline(0, system_coordinator_mock).name, str)
        assert isinstance(
            CircuitIsCoolingAllowed(0, 0, system_coordinator_mock).is_on, bool
        )
        assert isinstance(
            CircuitIsCoolingAllowed(0, 0, system_coordinator_mock).name, str
        )
        await mocked_api.aiohttp_session.close()
