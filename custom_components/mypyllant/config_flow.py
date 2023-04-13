from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.config_validation import positive_int
from myPyllant.api import AuthenticationFailed, LoginEndpointInvalid, MyPyllantAPI
from myPyllant.const import (
    BRANDS,
    COUNTRIES,
    DEFAULT_BRAND,
    DEFAULT_QUICK_VETO_DURATION,
)

from .const import (
    DEFAULT_COUNTRY,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_DEFAULT_QUICK_VETO_DURATION,
    OPTION_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.

_COUNTRIES_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v) for k, v in COUNTRIES.items()
]
_BRANDS_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v) for k, v in BRANDS.items()
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required(OPTION_COUNTRY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=_COUNTRIES_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Required(
            OPTION_BRAND,
            default=DEFAULT_BRAND,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=_BRANDS_OPTIONS,
                mode=selector.SelectSelectorMode.LIST,
            ),
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    api = MyPyllantAPI(
        data["username"], data["password"], data["country"], data["brand"]
    )
    await api.login()

    return {"title": data["username"]}


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        config_country = self.config_entry.data.get(OPTION_COUNTRY, DEFAULT_COUNTRY)
        config_brand = self.config_entry.data.get(OPTION_BRAND, DEFAULT_BRAND)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTION_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): positive_int,
                    vol.Required(
                        OPTION_DEFAULT_QUICK_VETO_DURATION,
                        default=self.config_entry.options.get(
                            OPTION_DEFAULT_QUICK_VETO_DURATION,
                            DEFAULT_QUICK_VETO_DURATION,
                        ),
                    ): positive_int,
                    vol.Required(
                        OPTION_COUNTRY,
                        default=self.config_entry.options.get(
                            OPTION_COUNTRY, config_country
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_COUNTRIES_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Required(
                        OPTION_BRAND,
                        default=self.config_entry.options.get(
                            OPTION_BRAND, config_brand
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_BRANDS_OPTIONS,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                }
            ),
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except AuthenticationFailed:
                errors["base"] = "authentication_failed"
            except LoginEndpointInvalid:
                errors["country"] = "login_endpoint_invalid"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
