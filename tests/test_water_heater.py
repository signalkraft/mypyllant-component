from unittest import mock

import pytest
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS

from custom_components.mypyllant.const import DOMAIN
from myPyllant.api import MyPyllantAPI
from myPyllant.enums import DHWOperationMode
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.water_heater import (
    DomesticHotWaterEntity,
    async_setup_entry,
)
from tests.conftest import MockConfigEntry, TEST_OPTIONS
from tests.test_init import test_user_input


@pytest.mark.parametrize("test_data", list_test_data())
async def test_async_setup_water_heater(
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
        if not system_coordinator_mock.data[0].domestic_hot_water:
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No DHW in system {system_coordinator_mock.data[0]}, skipping water heater tests"
            )
        hass.data[DOMAIN] = {
            config_entry.entry_id: {"system_coordinator": system_coordinator_mock}
        }
        async_add_entities_mock = mock.Mock(return_value=None)
        mock_async_register_entity_service = mock.Mock(return_value=None)
        with mock.patch(
            "homeassistant.helpers.entity_platform.async_get_current_platform",
            side_effect=lambda *args, **kwargs: mock_async_register_entity_service,
        ):
            await async_setup_entry(hass, config_entry, async_add_entities_mock)
        async_add_entities_mock.assert_called_once()
        assert len(async_add_entities_mock.call_args.args[0]) > 0
    await mocked_api.aiohttp_session.close()


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
        dhw = DomesticHotWaterEntity(0, 0, system_coordinator_mock, {})
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
            operation_mode=DHWOperationMode("OFF").display_value
        )
        system_coordinator_mock._debounced_refresh.async_cancel()

        await mocked_api.aiohttp_session.close()
