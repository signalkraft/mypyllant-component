from datetime import timedelta
from unittest import mock

import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import Circuit, DomesticHotWater, System, Zone
from myPyllant.tests.utils import _mocked_api, _mypyllant_aioresponses
from pydantic_factories import ModelFactory

from custom_components.mypyllant import SystemCoordinator


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


class SystemFactory(ModelFactory):
    __model__ = System


class ZoneFactory(ModelFactory):
    __model__ = Zone


class CircuitFactory(ModelFactory):
    __model__ = Circuit


class DomesticHotWaterFactory(ModelFactory):
    __model__ = DomesticHotWater


@pytest.fixture
def mypyllant_aioresponses():
    return _mypyllant_aioresponses()


@pytest.fixture
async def mocked_api() -> MyPyllantAPI:
    return await _mocked_api()


@pytest.fixture
async def system_coordinator_mock(hass, mocked_api):
    system_coordinator = SystemCoordinator(
        hass, mocked_api, mock.Mock(), timedelta(seconds=10)
    )
    system_coordinator.data = await system_coordinator._async_update_data()
    return system_coordinator
