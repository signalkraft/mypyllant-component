"""Tests for pyscript config flow."""
import logging
from unittest import mock

import pytest
from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import DATA_COMPONENTS, DATA_INTEGRATIONS
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.test_api import list_test_data

from custom_components.mypyllant import DOMAIN, async_setup_entry, async_unload_entry
from custom_components.mypyllant.config_flow import DATA_SCHEMA
from tests.conftest import TEST_OPTIONS, MockConfigEntry

_LOGGER = logging.getLogger(__name__)


data = {
    "username": "username",
    "password": "password",
    "country": "germany",
    "brand": "vaillant",
}


async def test_flow_init(hass):
    """Test the initial flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expected = {
        "data_schema": DATA_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": mock.ANY,
        "handler": "mypyllant",
        "step_id": "user",
        "type": "form",
        "last_step": None,
        "preview": None,
    }
    assert expected == result


async def test_user_flow_minimum_fields(hass: HomeAssistant):
    """Test user config flow with minimum fields."""
    # test form shows
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


@pytest.mark.parametrize("test_data", list_test_data())
async def test_async_setup(
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
            data=data,
            options=TEST_OPTIONS,
        )
        mock.patch("myPyllant.api.MyPyllantAPI", mocked_api)
        result = await async_setup_entry(hass, config_entry)
        assert result, "Component did not setup successfully"

        result = await async_unload_entry(hass, config_entry)
        assert result, "Component did not unload successfully"

    await mocked_api.aiohttp_session.close()
