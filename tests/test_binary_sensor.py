from datetime import timedelta
from unittest import mock

import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import Device, System
from myPyllant.tests.test_api import get_test_data

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.binary_sensor import (
    CircuitEntity,
    CircuitIsCoolingAllowed,
    ControlError,
    ControlOnline,
    SystemControlEntity,
)


@pytest.mark.parametrize("test_data", get_test_data())
async def test_system_binary_sensors(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        system = SystemControlEntity(0, system_coordinator)
        assert isinstance(system.primary_heat_generator, Device)
        assert isinstance(system.device_info, dict)

        circuit = CircuitEntity(0, 0, system_coordinator)
        assert isinstance(circuit.device_info, dict)
        assert isinstance(circuit.system, System)

        assert ControlError(0, system_coordinator).is_on is False
        assert isinstance(ControlError(0, system_coordinator).name, str)
        assert ControlOnline(0, system_coordinator).is_on is True
        assert isinstance(ControlOnline(0, system_coordinator).name, str)
        assert isinstance(CircuitIsCoolingAllowed(0, 0, system_coordinator).is_on, bool)
        assert isinstance(CircuitIsCoolingAllowed(0, 0, system_coordinator).name, str)
        await mocked_api.aiohttp_session.close()
