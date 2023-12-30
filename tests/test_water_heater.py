import pytest
from homeassistant.const import ATTR_TEMPERATURE
from myPyllant.api import MyPyllantAPI
from myPyllant.models import DHWOperationMode
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.water_heater import DomesticHotWaterEntity


@pytest.mark.parametrize("test_data", list_test_data())
async def test_water_heater(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )

        if not system_coordinator_mock.data[0].domestic_hot_water:
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No DHW in system {system_coordinator_mock.data[0]}, skipping water heater tests"
            )
        dhw = DomesticHotWaterEntity(0, 0, system_coordinator_mock)
        assert isinstance(dhw.device_info, dict)
        assert isinstance(dhw.min_temp, (int, float, complex))
        assert isinstance(dhw.max_temp, (int, float, complex))
        if "currentTemperature" in test_data:
            assert isinstance(dhw.current_temperature, (int, float, complex))
        assert isinstance(dhw.operation_list, list)
        assert isinstance(dhw.extra_state_attributes, dict)
        assert dhw.current_operation in dhw.operation_list

        await dhw.async_set_temperature(**{ATTR_TEMPERATURE: 50})
        await dhw.async_set_operation_mode(
            operation_mode=DHWOperationMode("MANUAL").display_value
        )
        system_coordinator_mock._debounced_refresh.async_cancel()

        await mocked_api.aiohttp_session.close()
