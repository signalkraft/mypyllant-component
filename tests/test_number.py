from unittest import mock

import pytest

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.number import (
    SystemManualCoolingDays,
    VentilationMaximumDayFanStage,
    VentilationMaximumNightFanStage,
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
@pytest.mark.parametrize(
    "number_class,fan_stage_type",
    [
        (VentilationMaximumDayFanStage, VentilationFanStageType.DAY),
        (VentilationMaximumNightFanStage, VentilationFanStageType.NIGHT),
    ],
)
async def test_ventilation_maximum_fan_stage(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
    test_data_path,
    number_class,
    fan_stage_type,
):
    test_data = load_test_data(DATA_DIR / test_data_path)
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        number = number_class(0, 0, system_coordinator_mock)
        ventilation = number.ventilation
        assert number.native_value == getattr(
            ventilation, f"maximum_{fan_stage_type.lower()}_fan_stage"
        )
        assert isinstance(number.native_value, int)
        assert fan_stage_type.title() in number.name
        assert number.unique_id.endswith(f"_maximum_{fan_stage_type.lower()}_fan_stage")
        assert isinstance(number.device_info, dict)
        # State must be the numeric value, not a climate HVAC mode
        assert number.state == number.native_value

        with mock.patch.object(
            system_coordinator_mock.api, "set_ventilation_fan_stage"
        ) as mock_set:
            await number.async_set_native_value(3.0)
            mock_set.assert_awaited_once_with(ventilation, 3, fan_stage_type)
        system_coordinator_mock._debounced_refresh.async_cancel()
    await mocked_api.aiohttp_session.close()
