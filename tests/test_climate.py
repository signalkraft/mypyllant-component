from datetime import timedelta
from unittest import mock

import pytest as pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.test_api import list_test_data

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.climate import ZoneClimate


@pytest.mark.parametrize("test_data", list_test_data())
async def test_zone_climate(
    hass, mypyllant_aioresponses, mocked_api: MyPyllantAPI, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = SystemCoordinator(
            hass, mocked_api, mock.Mock(), timedelta(seconds=10)
        )
        system_coordinator.data = await system_coordinator._async_update_data()
        climate = ZoneClimate(0, 0, system_coordinator, 3)
        assert isinstance(climate.device_info, dict)
        assert isinstance(climate.target_temperature, float)
        zone_state = [
            z for z in system_coordinator.data[0].state["zones"] if z["index"] == 0
        ][0]
        if "currentRoomTemperature" in zone_state:
            assert isinstance(climate.current_temperature, float)
        else:
            pytest.skip(f"No currentRoomTemperature in {zone_state}, skipping")
        if "humidity" in zone_state:
            assert isinstance(climate.current_humidity, float)
        else:
            pytest.skip(f"No humidity in {zone_state}, skipping")
        assert isinstance(climate.preset_modes, list)
        assert climate.hvac_mode in climate.hvac_modes
        assert climate.preset_mode in climate.preset_modes
        await mocked_api.aiohttp_session.close()
