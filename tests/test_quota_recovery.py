from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from aiohttp import RequestInfo
from aiohttp.client_exceptions import ClientResponseError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mypyllant.const import (
    API_DOWN_PAUSE_INTERVAL,
    DOMAIN,
    QUOTA_PAUSE_INTERVAL,
)
from custom_components.mypyllant.coordinator import DailyDataCoordinator
from custom_components.mypyllant.sensor import (
    DAILY_SENSORS_RETRY_INTERVAL,
    async_add_daily_sensors_when_ready,
)
from custom_components.mypyllant.utils import extract_quota_duration


def quota_error(duration: str) -> ClientResponseError:
    return ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/",  # type: ignore
            method="GET",
            headers=None,  # type: ignore
        ),
        history=None,  # type: ignore
        status=403,
        message=f"Out of call volume quota. Quota will be replenished in {duration}.",
    )


@pytest.mark.parametrize(
    "duration,seconds",
    [
        ("00:44:32", 2672),
        ("04:16:47", 15407),
        ("1.02:02:00", 93720),
        ("5.12:32:57", 477177),
        ("12.00:00:01", 1036801),
    ],
)
def test_extract_quota_duration_with_days(duration, seconds):
    assert extract_quota_duration(quota_error(duration)) == seconds


@pytest.fixture
def daily_setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {entry.entry_id: {}}
    coordinator = DailyDataCoordinator(hass, mock.Mock(), entry, None)
    hass.data[DOMAIN][entry.entry_id]["daily_data_coordinator"] = coordinator
    return entry, coordinator


async def test_daily_sensors_added_after_recovery(hass, daily_setup):
    entry, coordinator = daily_setup
    add_entities = mock.Mock()
    async_add_daily_sensors_when_ready(hass, entry, coordinator, add_entities)
    assert coordinator.update_interval == DAILY_SENSORS_RETRY_INTERVAL

    coordinator.async_set_updated_data({})
    await hass.async_block_till_done()
    add_entities.assert_not_called()

    with mock.patch(
        "custom_components.mypyllant.sensor.create_daily_data_sensors",
        new=mock.AsyncMock(return_value=["sensor"]),
    ):
        coordinator.async_set_updated_data({"system": {"devices_data": []}})
        await hass.async_block_till_done()
        coordinator.async_set_updated_data({"system": {"devices_data": []}})
        await hass.async_block_till_done()

    add_entities.assert_called_once_with(["sensor"])
    assert coordinator.update_interval is None
    assert not coordinator._listeners


async def test_daily_sensors_keep_configured_interval(hass, daily_setup):
    entry, coordinator = daily_setup
    coordinator.update_interval = timedelta(hours=6)
    async_add_daily_sensors_when_ready(hass, entry, coordinator, mock.Mock())
    assert coordinator.update_interval == timedelta(hours=6)
    for unload in entry._on_unload:
        unload()
    assert not coordinator._listeners


async def test_setup_retry_delay(hass, daily_setup):
    _, coordinator = daily_setup
    assert coordinator.setup_retry_delay() == API_DOWN_PAUSE_INTERVAL
    coordinator._quota_exc_info = quota_error("bad")
    assert coordinator.setup_retry_delay() == QUOTA_PAUSE_INTERVAL
    coordinator._quota_end_time = datetime.now(timezone.utc) + timedelta(hours=26)
    assert 26 * 3600 <= coordinator.setup_retry_delay() <= 26 * 3600 + 60
