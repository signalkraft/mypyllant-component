import pytest as pytest
from homeassistant.components.climate import HVACMode
from homeassistant.components.climate.const import PRESET_AWAY
from homeassistant.const import ATTR_TEMPERATURE
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.test_api import list_test_data

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.climate import ZoneClimate


@pytest.mark.parametrize("test_data", list_test_data())
async def test_zone_climate(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        climate = ZoneClimate(0, 0, system_coordinator_mock, 3)
        assert isinstance(climate.device_info, dict)
        assert isinstance(climate.extra_state_attributes, dict)
        assert isinstance(climate.target_temperature, float)

        await climate.set_holiday()
        await climate.cancel_holiday()
        await climate.set_quick_veto()
        await climate.async_set_hvac_mode(HVACMode.AUTO)
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 20})
        # TODO: Test logic of different calls depending on current new preset mode
        await climate.async_set_preset_mode(preset_mode=PRESET_AWAY)
        system_coordinator_mock._debounced_refresh.async_cancel()

        zone_state = [
            z for z in system_coordinator_mock.data[0].state["zones"] if z["index"] == 0
        ][0]
        if "currentRoomTemperature" in zone_state:
            assert isinstance(climate.current_temperature, float)
        if "humidity" in zone_state:
            assert isinstance(climate.current_humidity, float)
        assert isinstance(climate.preset_modes, list)
        assert climate.hvac_mode in climate.hvac_modes
        assert climate.preset_mode in climate.preset_modes
        await mocked_api.aiohttp_session.close()
