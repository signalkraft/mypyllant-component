from datetime import timedelta
from unittest import mock

import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import Circuit, DomesticHotWater, System, Zone
from myPyllant.tests.utils import _mocked_api, _mypyllant_aioresponses
from polyfactory.factories import DataclassFactory

from custom_components.mypyllant import DOMAIN, DailyDataCoordinator, SystemCoordinator


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
        hass.data = {
            DOMAIN: {
                entry.entry_id: {
                    "quota_time": None,
                    "quota_exc_info": None,
                }
            }
        }
        return SystemCoordinator(hass, mocked_api, entry, timedelta(seconds=10))


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
