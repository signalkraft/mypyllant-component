import pytest as pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import VentilationOperationMode
from myPyllant.tests.test_api import list_test_data

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.fan import VentilationFan


@pytest.mark.parametrize("test_data", list_test_data())
async def test_ventilation_fan(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        if not system_coordinator_mock.data[0].ventilation:
            await mocked_api.aiohttp_session.close()
            pytest.skip("No ventilation entity in system")

        ventilation = VentilationFan(
            0,
            0,
            system_coordinator_mock,
        )
        assert isinstance(ventilation.device_info, dict)
        assert isinstance(ventilation.extra_state_attributes, dict)
        assert isinstance(ventilation.preset_mode, str)
        assert isinstance(ventilation.percentage, int)

        await ventilation.async_set_preset_mode(str(VentilationOperationMode.REDUCED))
        await ventilation.async_set_percentage(0)
        await ventilation.async_set_percentage(25)
        await ventilation.async_set_percentage(50)
        await ventilation.async_set_percentage(100)
        system_coordinator_mock._debounced_refresh.async_cancel()
        await mocked_api.aiohttp_session.close()
