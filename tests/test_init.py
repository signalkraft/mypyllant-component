"""Tests for pyscript config flow."""

import logging
from unittest import mock

from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from myPyllant.api import MyPyllantAPI
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import load_test_data

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant import async_setup_entry, async_unload_entry
from custom_components.mypyllant.config_flow import DATA_SCHEMA
from tests.utils import get_config_entry, test_user_input

_LOGGER = logging.getLogger(__name__)


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
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=test_user_input,
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM


async def test_async_setup(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
):
    test_data = load_test_data(DATA_DIR / "heatpump_heat_curve")
    with mypyllant_aioresponses(test_data) as _:
        config_entry = get_config_entry()
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        mock.patch("myPyllant.api.MyPyllantAPI", mocked_api)
        result = await async_setup_entry(hass, config_entry)
        assert result, "Component did not setup successfully"

        result = await async_unload_entry(hass, config_entry)
        assert result, "Component did not unload successfully"

    await mocked_api.aiohttp_session.close()
