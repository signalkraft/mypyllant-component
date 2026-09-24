from unittest import mock

import pytest

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.number import (
    SystemManualCoolingDays,
    VentilationMaximumDayFanStageNumber,
    VentilationMaximumNightFanStageNumber,
)
from myPyllant.api import MyPyllantAPI
from myPyllant.enums import VentilationFanStageType
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


@pytest.mark.parametrize(
    "test_data_path",
    ["ventilation", "vrc700_ventilation.yaml"],
)
async def test_ventilation_maximum_fan_stage_numbers(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
    test_data_path,
):
    test_data = load_test_data(DATA_DIR / test_data_path)
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        ventilation = system_coordinator_mock.data[0].ventilation[0]

        day_number = VentilationMaximumDayFanStageNumber(
            0, 0, system_coordinator_mock
        )
        night_number = VentilationMaximumNightFanStageNumber(
            0, 0, system_coordinator_mock
        )

        assert day_number.native_min_value == 1
        assert day_number.native_max_value == 6
        assert day_number.native_step == 1
        assert day_number.native_value == ventilation.maximum_day_fan_stage
        assert night_number.native_value == ventilation.maximum_night_fan_stage
        assert isinstance(day_number.device_info, dict)
        assert day_number.unique_id != night_number.unique_id

        with mock.patch.object(
            system_coordinator_mock.api, "set_ventilation_fan_stage"
        ) as mock_set:
            await day_number.async_set_native_value(3)
            assert mock_set.await_args is not None
            assert mock_set.await_args.args[0] == ventilation
            assert mock_set.await_args.args[1] == 3
            assert mock_set.await_args.args[2] == VentilationFanStageType.DAY

        with mock.patch.object(
            system_coordinator_mock.api, "set_ventilation_fan_stage"
        ) as mock_set:
            await night_number.async_set_native_value(5)
            assert mock_set.await_args is not None
            assert mock_set.await_args.args[0] == ventilation
            assert mock_set.await_args.args[1] == 5
            assert mock_set.await_args.args[2] == VentilationFanStageType.NIGHT

        system_coordinator_mock._debounced_refresh.async_cancel()
        await mocked_api.aiohttp_session.close()
