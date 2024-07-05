from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.number import SystemManualCoolingDays
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import load_test_data


async def test_manual_cooling_days(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
):
    test_data = load_test_data(DATA_DIR / "ventilation")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert system_coordinator_mock.data[0].is_cooling_allowed is True
        manual_cooling = SystemManualCoolingDays(0, system_coordinator_mock)
        assert manual_cooling.native_value == 0
        await mocked_api.aiohttp_session.close()
