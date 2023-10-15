import uuid
from datetime import timedelta
from unittest import mock

import pytest
from homeassistant import config_entries
from myPyllant.api import MyPyllantAPI
from myPyllant.const import DEFAULT_BRAND
from myPyllant.models import Circuit, DomesticHotWater, System, Zone
from myPyllant.tests.utils import _mocked_api, _mypyllant_aioresponses
from polyfactory.factories import DataclassFactory

from custom_components.mypyllant import (
    DEFAULT_COUNTRY,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_REFRESH_DELAY,
    OPTION_UPDATE_INTERVAL,
    DailyDataCoordinator,
    SystemCoordinator,
)

TEST_OPTIONS = {
    OPTION_COUNTRY: DEFAULT_COUNTRY,
    OPTION_BRAND: DEFAULT_BRAND,
    OPTION_REFRESH_DELAY: 0,
    OPTION_UPDATE_INTERVAL: 1,
}


class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


class SystemFactory(DataclassFactory):
    __model__ = System


class ZoneFactory(DataclassFactory):
    __model__ = Zone


class CircuitFactory(DataclassFactory):
    __model__ = Circuit


class DomesticHotWaterFactory(DataclassFactory):
    __model__ = DomesticHotWater


@pytest.fixture
def mypyllant_aioresponses():
    return _mypyllant_aioresponses()


@pytest.fixture
async def mocked_api() -> MyPyllantAPI:
    return await _mocked_api()


@pytest.fixture
async def system_coordinator_mock(hass, mocked_api) -> SystemCoordinator:
    with mock.patch(
        "homeassistant.config_entries.ConfigEntry",
        new_callable=mock.PropertyMock,
        return_value="mockid",
    ) as entry:
        entry.options = TEST_OPTIONS
        hass.data = {
            DOMAIN: {
                entry.entry_id: {
                    "quota_time": None,
                    "quota_exc_info": None,
                }
            }
        }
        return SystemCoordinator(hass, mocked_api, entry, update_interval=None)


@pytest.fixture
async def daily_data_coordinator_mock(hass, mocked_api) -> DailyDataCoordinator:
    with mock.patch(
        "homeassistant.config_entries.ConfigEntry",
        new_callable=mock.PropertyMock,
        return_value="mockid",
    ) as entry:
        hass.data = {
            DOMAIN: {
                entry.entry_id: {
                    "quota_time": None,
                    "quota_exc_info": None,
                }
            }
        }
        return DailyDataCoordinator(hass, mocked_api, entry, timedelta(seconds=10))


class MockConfigEntry(config_entries.ConfigEntry):
    """Helper for creating config entries that adds some defaults."""

    def __init__(
        self,
        *,
        domain="test",
        data=None,
        version=1,
        entry_id=None,
        source=config_entries.SOURCE_USER,
        title="Mock Title",
        state=None,
        options={},
        pref_disable_new_entities=None,
        pref_disable_polling=None,
        unique_id=None,
        disabled_by=None,
        reason=None,
    ):
        """Initialize a mock config entry."""
        kwargs = {
            "entry_id": entry_id or uuid.uuid4(),
            "domain": domain,
            "data": data or {},
            "pref_disable_new_entities": pref_disable_new_entities,
            "pref_disable_polling": pref_disable_polling,
            "options": options,
            "version": version,
            "title": title,
            "unique_id": unique_id,
            "disabled_by": disabled_by,
        }
        if source is not None:
            kwargs["source"] = source
        if state is not None:
            kwargs["state"] = state
        super().__init__(**kwargs)
        if reason is not None:
            self.reason = reason

    def add_to_hass(self, hass):
        """Test helper to add entry to hass."""
        hass.config_entries._entries[self.entry_id] = self
        hass.config_entries._domain_index.setdefault(self.domain, []).append(
            self.entry_id
        )

    def add_to_manager(self, manager):
        """Test helper to add entry to entry manager."""
        manager._entries[self.entry_id] = self
        manager._domain_index.setdefault(self.domain, []).append(self.entry_id)
