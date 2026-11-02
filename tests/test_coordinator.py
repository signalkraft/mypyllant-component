"""Tests for coordinator refresh scheduling."""

from datetime import timedelta
from unittest.mock import Mock

from myPyllant.api import MyPyllantAPI
from tests.utils import get_config_entry

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.coordinator import DailyDataCoordinator


async def test_daily_data_coordinator_schedules_configured_interval(
    hass, mocked_api: MyPyllantAPI
):
    entry = get_config_entry()
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    coordinator = DailyDataCoordinator(
        hass, mocked_api, entry, update_interval=timedelta(seconds=3600)
    )
    assert coordinator.config_entry is entry

    remove_listener = coordinator.async_add_listener(Mock())
    assert coordinator._unsub_refresh is not None

    remove_listener()
    assert coordinator._unsub_refresh is None

    coordinator_without_interval = DailyDataCoordinator(
        hass, mocked_api, entry, update_interval=None
    )
    remove_listener = coordinator_without_interval.async_add_listener(Mock())
    assert coordinator_without_interval._unsub_refresh is None
    remove_listener()
