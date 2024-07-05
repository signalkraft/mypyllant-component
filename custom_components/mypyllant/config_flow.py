from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.config_validation import positive_int
from myPyllant.api import (
    MyPyllantAPI,
)
from myPyllant.http_client import (
    AuthenticationFailed,
    LoginEndpointInvalid,
    RealmInvalid,
)
from myPyllant.const import (
    BRANDS,
    COUNTRIES,
    DEFAULT_BRAND,
    DEFAULT_QUICK_VETO_DURATION,
    DEFAULT_HOLIDAY_DURATION,
)
from . import OPTION_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY

from .const import (
    DEFAULT_COUNTRY,
    DEFAULT_REFRESH_DELAY,
    DEFAULT_TIME_PROGRAM_OVERWRITE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_DEFAULT_QUICK_VETO_DURATION,
    OPTION_REFRESH_DELAY,
    OPTION_TIME_PROGRAM_OVERWRITE,
    OPTION_UPDATE_INTERVAL,
    OPTION_DEFAULT_HOLIDAY_DURATION,
    OPTION_DEFAULT_HOLIDAY_SETPOINT,
    DEFAULT_HOLIDAY_SETPOINT,
    OPTION_FETCH_RTS,
    DEFAULT_FETCH_RTS,
    OPTION_FETCH_MPC,
    DEFAULT_FETCH_MPC,
    OPTION_FETCH_AMBISENSE_ROOMS,
    DEFAULT_FETCH_AMBISENSE_ROOMS,
    OPTION_FETCH_ENERGY_MANAGEMENT,
    DEFAULT_FETCH_ENERGY_MANAGEMENT,
    OPTION_FETCH_EEBUS,
    DEFAULT_FETCH_EEBUS,
    OPTION_DEFAULT_MANUAL_COOLING_DURATION,
    DEFAULT_MANUAL_COOLING_DURATION,
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
    selector.SelectOptionDict(value=k, label=v)
    for k, v in COUNTRIES[DEFAULT_BRAND].items()
]
_BRANDS_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v) for k, v in BRANDS.items()
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required(
            OPTION_BRAND,
            default=DEFAULT_BRAND,
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=_BRANDS_OPTIONS,
                mode=selector.SelectSelectorMode.LIST,
            ),
        ),
        vol.Optional(OPTION_COUNTRY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=_COUNTRIES_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
    },
)


async def validate_input(hass: HomeAssistant, data: dict) -> str:
    async with MyPyllantAPI(**data) as api:
        await api.login()
        return data["username"].lower()


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
                        OPTION_UPDATE_INTERVAL_DAILY,
                        default=self.config_entry.options.get(
                            OPTION_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY
                        ),
                    ): positive_int,
                    vol.Required(
                        OPTION_REFRESH_DELAY,
                        default=self.config_entry.options.get(
                            OPTION_REFRESH_DELAY, DEFAULT_REFRESH_DELAY
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
                        OPTION_DEFAULT_HOLIDAY_DURATION,
                        default=self.config_entry.options.get(
                            OPTION_DEFAULT_HOLIDAY_DURATION,
                            DEFAULT_HOLIDAY_DURATION,
                        ),
                    ): positive_int,
                    vol.Required(
                        OPTION_DEFAULT_HOLIDAY_SETPOINT,
                        default=self.config_entry.options.get(
                            OPTION_DEFAULT_HOLIDAY_SETPOINT,
                            DEFAULT_HOLIDAY_SETPOINT,
                        ),
                    ): vol.All(vol.Coerce(float), vol.Clamp(min=0, max=30)),
                    vol.Required(
                        OPTION_DEFAULT_MANUAL_COOLING_DURATION,
                        default=self.config_entry.options.get(
                            OPTION_DEFAULT_MANUAL_COOLING_DURATION,
                            DEFAULT_MANUAL_COOLING_DURATION,
                        ),
                    ): positive_int,
                    vol.Required(
                        OPTION_TIME_PROGRAM_OVERWRITE,
                        default=self.config_entry.options.get(
                            OPTION_TIME_PROGRAM_OVERWRITE,
                            DEFAULT_TIME_PROGRAM_OVERWRITE,
                        ),
                    ): bool,
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
                    vol.Optional(
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
                        OPTION_FETCH_RTS,
                        default=self.config_entry.options.get(
                            OPTION_FETCH_RTS,
                            DEFAULT_FETCH_RTS,
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_FETCH_MPC,
                        default=self.config_entry.options.get(
                            OPTION_FETCH_MPC,
                            DEFAULT_FETCH_MPC,
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_FETCH_AMBISENSE_ROOMS,
                        default=self.config_entry.options.get(
                            OPTION_FETCH_AMBISENSE_ROOMS,
                            DEFAULT_FETCH_AMBISENSE_ROOMS,
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_FETCH_ENERGY_MANAGEMENT,
                        default=self.config_entry.options.get(
                            OPTION_FETCH_ENERGY_MANAGEMENT,
                            DEFAULT_FETCH_ENERGY_MANAGEMENT,
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_FETCH_EEBUS,
                        default=self.config_entry.options.get(
                            OPTION_FETCH_EEBUS,
                            DEFAULT_FETCH_EEBUS,
                        ),
                    ): bool,
                }
            ),
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    VERSION = 1  # This needs to be changed if a migration is necessary
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
                username = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(username)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=username, data=user_input)
            except AuthenticationFailed:
                errors["base"] = "authentication_failed"
            except LoginEndpointInvalid:
                errors["country"] = "login_endpoint_invalid"
            except RealmInvalid:
                errors["country"] = "realm_invalid"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
