from __future__ import annotations

import logging
from typing import Any

from myPyllant.api import MyPyllantAPI
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.config_validation import positive_int

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, OPTION_UPDATE_INTERVAL

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
DATA_SCHEMA = vol.Schema({vol.Required("username"): str, vol.Required("password"): str})


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    api = MyPyllantAPI(data["username"], data["password"])
    try:
        await api.login()
    except Exception:
        raise AuthenticationFailed
    finally:
        await api.aiohttp_session.close()

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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTION_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): positive_int
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
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except AuthenticationFailed:
                errors["host"] = "authentication_failed"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AuthenticationFailed(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
