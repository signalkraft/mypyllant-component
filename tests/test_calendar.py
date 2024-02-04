from datetime import datetime, timedelta, timezone

import freezegun
import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.calendar import (
    ZoneHeatingCalendar,
    DomesticHotWaterCalendar,
)


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
