from unittest.mock import Mock

import pytest
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS

from custom_components.mypyllant import SystemCoordinator
from myPyllant.api import MyPyllantAPI
from myPyllant.models import System
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import list_test_data, load_test_data

from custom_components.mypyllant.binary_sensor import (
    CircuitEntity,
    CircuitIsCoolingAllowed,
    ControlError,
    ControlOnline,
    SystemControlEntity,
    async_setup_entry,
)
from custom_components.mypyllant.const import DOMAIN
from tests.conftest import MockConfigEntry, TEST_OPTIONS
from tests.test_init import test_user_input


@pytest.mark.parametrize("test_data", list_test_data())
async def test_async_setup_binary_sensors(
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
        mock = Mock(return_value=None)
        await async_setup_entry(hass, config_entry, mock)
        mock.assert_called_once()
        assert len(mock.call_args.args[0]) > 0

        await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_system_binary_sensors(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock, test_data
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        system = SystemControlEntity(0, system_coordinator_mock)
        assert isinstance(system.device_info, dict)

        circuit = CircuitEntity(0, 0, system_coordinator_mock)
        assert isinstance(circuit.device_info, dict)
        assert isinstance(circuit.system, System)

        assert ControlError(0, system_coordinator_mock).is_on is False
        assert isinstance(ControlError(0, system_coordinator_mock).name, str)
        assert ControlOnline(0, system_coordinator_mock).is_on is True
        assert isinstance(ControlOnline(0, system_coordinator_mock).name, str)
        assert isinstance(
            CircuitIsCoolingAllowed(0, 0, system_coordinator_mock).is_on, bool
        )
        assert isinstance(
            CircuitIsCoolingAllowed(0, 0, system_coordinator_mock).name, str
        )
        await mocked_api.aiohttp_session.close()


async def test_control_error(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
):
    test_data = load_test_data(DATA_DIR / "ambisense2.yml")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        control_error = ControlError(0, system_coordinator_mock)
        assert control_error.is_on
        await mocked_api.aiohttp_session.close()
