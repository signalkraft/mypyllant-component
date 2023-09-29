import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.test_api import list_test_data

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
            pytest.skip(
                f"No DHW in system {system_coordinator_mock.data[0]}, skipping water heater tests"
            )
        dhw = DomesticHotWaterEntity(0, 0, system_coordinator_mock)
        assert isinstance(dhw.device_info, dict)
        assert isinstance(dhw.target_temperature, float)
        if "currentTemperature" in test_data:
            assert isinstance(dhw.current_temperature, float)
        assert isinstance(dhw.operation_list, list)
        assert dhw.current_operation in dhw.operation_list
        await mocked_api.aiohttp_session.close()
