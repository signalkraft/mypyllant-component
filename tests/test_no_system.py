"""Tests for fixtures that yield no System objects.

These cover the case where every home in the test data has an unsupported
control identifier.  The upstream API skips such homes (api.get_systems uses
`if control_identifier.is_unsupported: continue`), so coordinator.data is
empty — and DailyDataCoordinator raises UpdateFailed explicitly.

Using list_test_data(only_with_systems=False) targets exactly these fixtures
so the regular parametrized tests can require non-empty coordinator.data
without worrying about silently masking real failures.
"""

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from myPyllant.api import MyPyllantAPI
from myPyllant.tests.utils import list_test_data


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=False))
async def test_unsupported_control_identifier_yields_no_systems(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    """SystemCoordinator.data must be empty when all homes have unsupported identifiers."""
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        assert system_coordinator_mock.data == [], (
            f"Expected no systems for {test_data['_directory']}, "
            f"got {system_coordinator_mock.data}"
        )
    await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=False))
async def test_daily_data_coordinator_fails_without_systems(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    daily_data_coordinator_mock,
    test_data,
):
    """DailyDataCoordinator must raise UpdateFailed when no systems are available."""
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = daily_data_coordinator_mock.hass_data["system_coordinator"]
        system_coordinator.data = await system_coordinator._async_update_data()
        assert system_coordinator.data == []
        with pytest.raises(UpdateFailed):
            await daily_data_coordinator_mock._async_update_data()
    await mocked_api.aiohttp_session.close()
