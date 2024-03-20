from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import freezegun
import pytest
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS

from custom_components.mypyllant.const import DOMAIN
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import list_test_data, load_test_data

from custom_components.mypyllant.calendar import (
    ZoneHeatingCalendar,
    DomesticHotWaterCalendar,
    async_setup_entry,
    DomesticHotWaterCirculationCalendar,
)
from tests.conftest import MockConfigEntry, TEST_OPTIONS
from tests.test_init import test_user_input


@pytest.mark.parametrize("test_data", list_test_data())
async def test_async_setup_calendar(
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
async def test_zone_heating_calendar(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        calendar = ZoneHeatingCalendar(0, 0, system_coordinator_mock)
        if not calendar.time_program.has_time_program:
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No time program in zone {system_coordinator_mock.data[0].zones[0]}, skipping calendar test"
            )
        with freezegun.freeze_time("2023-01-01T00:00:00+00:00"):
            events = await calendar.async_get_events(
                hass,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) + timedelta(days=7),
            )
            assert len(events) > 0
            assert calendar.event is not None
    await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_dhw_calendar(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        if not system_coordinator_mock.data[0].domestic_hot_water:
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No DHW in system {system_coordinator_mock.data[0]}, skipping calendar test"
            )
        if (
            not system_coordinator_mock.data[0]
            .domestic_hot_water[0]
            .time_program_dhw.has_time_program
        ):
            await mocked_api.aiohttp_session.close()
            pytest.skip(
                f"No time program in DHW {system_coordinator_mock.data[0].domestic_hot_water[0]}, skipping calendar test"
            )

        calendar = DomesticHotWaterCalendar(0, 0, system_coordinator_mock)
        with freezegun.freeze_time("2023-01-01T00:00:00+00:00"):
            events = await calendar.async_get_events(
                hass,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) + timedelta(days=7),
            )
            assert len(events) > 0
            assert calendar.event is not None
    await mocked_api.aiohttp_session.close()


async def test_dhw_circulation_calendar(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
):
    test_data = load_test_data(DATA_DIR / "vrc700_dhw.yaml")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        calendar = DomesticHotWaterCirculationCalendar(0, 0, system_coordinator_mock)
        with freezegun.freeze_time("2023-01-01T00:00:00+00:00"):
            events = await calendar.async_get_events(
                hass,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) + timedelta(days=7),
            )
            assert len(events) > 0
            assert calendar.event is not None
    await mocked_api.aiohttp_session.close()


async def test_dhw_no_circulation_calendar(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
):
    test_data = load_test_data(DATA_DIR / "heatpump_electric_backup")
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        calendar = DomesticHotWaterCirculationCalendar(0, 0, system_coordinator_mock)
        with freezegun.freeze_time("2023-01-01T00:00:00+00:00"):
            events = await calendar.async_get_events(
                hass,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) + timedelta(days=7),
            )
            assert len(events) == 0
            assert calendar.event is None
    await mocked_api.aiohttp_session.close()
