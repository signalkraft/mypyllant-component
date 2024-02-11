from unittest import mock

import pytest as pytest
from homeassistant.components.climate import HVACMode
from homeassistant.components.climate.const import FAN_OFF, PRESET_AWAY
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS

from myPyllant.api import MyPyllantAPI
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant import SystemCoordinator, DOMAIN
from custom_components.mypyllant.climate import (
    VentilationClimate,
    ZoneClimate,
    async_setup_entry,
)
from tests.utils import get_config_entry
from tests.conftest import MockConfigEntry, TEST_OPTIONS
from tests.test_init import test_user_input


@pytest.mark.parametrize("test_data", list_test_data())
async def test_async_setup_climate(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    hass.data[DATA_COMPONENTS] = {}
    hass.data[DATA_INTEGRATIONS] = {}
    hass.data[DATA_REGISTRY] = EntityRegistry(hass)
    with mypyllant_aioresponses(test_data) as _:
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Mock Title",
            data=test_user_input,
            options=TEST_OPTIONS,
        )
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        hass.data[DOMAIN] = {
            config_entry.entry_id: {"system_coordinator": system_coordinator_mock}
        }
        mock_async_register_entity_service = mock.Mock(return_value=None)
        async_add_entities_mock = mock.Mock(return_value=None)
        with mock.patch(
            "homeassistant.helpers.entity_platform.async_get_current_platform",
            side_effect=lambda *args, **kwargs: mock_async_register_entity_service,
        ):
            await async_setup_entry(hass, config_entry, async_add_entities_mock)
        async_add_entities_mock.assert_called()
    await mocked_api.aiohttp_session.close()


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
        climate = ZoneClimate(
            0,
            0,
            system_coordinator_mock,
            get_config_entry(),
        )
        assert isinstance(climate.device_info, dict)
        assert isinstance(climate.extra_state_attributes, dict)
        assert isinstance(climate.target_temperature, float | int)
        assert isinstance(climate.extra_state_attributes, dict)

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


@pytest.mark.parametrize("test_data", list_test_data())
async def test_ventilation_climate(
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

        ventilation = VentilationClimate(
            0,
            0,
            system_coordinator_mock,
        )
        assert isinstance(ventilation.device_info, dict)
        assert isinstance(ventilation.extra_state_attributes, dict)
        assert isinstance(ventilation.hvac_mode, HVACMode)
        assert isinstance(ventilation.fan_mode, str)

        await ventilation.async_set_fan_mode(FAN_OFF)
        system_coordinator_mock._debounced_refresh.async_cancel()
        await mocked_api.aiohttp_session.close()
