"""Tests for pyscript config flow."""
import logging
from unittest import mock

from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER

from custom_components.mypyllant import DOMAIN
from custom_components.mypyllant.config_flow import DATA_SCHEMA

_LOGGER = logging.getLogger(__name__)


async def test_flow_init(hass):
    """Test the initial flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
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
    }
    assert expected == result


async def test_user_flow_minimum_fields(hass):
    """Test user config flow with minimum fields."""
    # test form shows
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "username": "username",
            "password": "password",
            "country": "germany",
            "brand": "vaillant",
        },
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
