from datetime import timedelta
from unittest import mock

import pytest
from myPyllant.tests.test_api import get_test_data

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.water_heater import DomesticHotWaterEntity


@pytest.mark.parametrize("test_data", get_test_data())
async def test_water_heater(hass, mypyllant_aioresponses, mocked_api, test_data):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()

        dhw = DomesticHotWaterEntity(0, 0, system_coordinator)
        assert isinstance(dhw.device_info, dict)
        assert isinstance(dhw.target_temperature, float)
        if "currentTemperature" in test_data:
            assert isinstance(dhw.current_temperature, float)
        assert isinstance(dhw.operation_list, list)
        assert dhw.current_operation in dhw.operation_list
        await mocked_api.aiohttp_session.close()
