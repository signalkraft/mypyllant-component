from __future__ import annotations

import logging
from datetime import datetime as dt, timedelta
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    SupportsResponse,
    ServiceCall,
    ServiceResponse,
)
from homeassistant.helpers import selector
from homeassistant.helpers.template import as_datetime
from homeassistant.helpers.entity_registry import async_migrate_entries, RegistryEntry
from homeassistant.core import callback

from myPyllant import export, report

from myPyllant.api import MyPyllantAPI
from myPyllant.const import DEFAULT_BRAND
from myPyllant.models import DeviceDataBucketResolution
from myPyllant.tests import generate_test_data

from custom_components.mypyllant.coordinator import (
    DeviceDataCoordinator,
    SystemCoordinator,
)

from custom_components.mypyllant.utils import async_remove_orphaned_devices

from .const import (
    DEFAULT_COUNTRY,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_UPDATE_INTERVAL,
    SERVICE_GENERATE_TEST_DATA,
    SERVICE_EXPORT,
    SERVICE_REPORT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.CLIMATE,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER,
]

_DEVICE_DATA_BUCKET_RESOLUTION_OPTIONS = [
    selector.SelectOptionDict(value=v.value, label=v.value.title())
    for v in DeviceDataBucketResolution
]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        """
        from homeassistant.helpers.device_registry import async_entries_for_config_entry

        devices = async_entries_for_config_entry(
            hass.data["device_registry"], config_entry.entry_id
        )
        """

        @callback
        def update_unique_id(entity_entry: RegistryEntry):
            # All entities which are bound to system needs to be starting with {system_id}_home
            if entity_entry.unique_id.count(
                "_"
            ) == 4 and entity_entry.unique_id.endswith("_heating_energy_efficiency"):
                return {
                    "new_unique_id": entity_entry.unique_id.replace(
                        "_heating_energy_efficiency", "_home_heating_energy_efficiency"
                    )
                }
            # old: {DOMAIN} {self.system.id} => {DOMAIN}_{self.system.id}
            if entity_entry.unique_id.count(
                "_"
            ) == 4 and entity_entry.unique_id.endswith("_cooling_allowed"):
                return {"new_unique_id": entity_entry.unique_id.replace(" ", "_")}

            # old: {DOMAIN}_{self.system.id}_{self.device.device_uuid}_{self.da_index} => {DOMAIN}_{self.system.id}_device_{self.device.device_uuid}_{self.da_index}
            sep = entity_entry.unique_id.split("_")
            if len(sep) == 4 and len(sep[3]) == 1 and sep[3].isnumeric():
                return {"new_unique_id": f"{sep[0]}_{sep[1]}_device_{sep[2]}_{sep[3]}"}
            return None

        await async_migrate_entries(hass, config_entry.entry_id, update_unique_id)
        config_entry.version = 2  # set to new version

    _LOGGER.debug("Migration to version %s successful", config_entry.version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if _LOGGER.isEnabledFor(logging.DEBUG):
        from importlib.metadata import version

        _LOGGER.debug(
            "Starting mypyllant component %s (library %s) with homeassistant %s, dacite %s, and aiohttp %s",
            hass.data["integrations"][DOMAIN].version,
            version("myPyllant"),
            version("homeassistant"),
            version("dacite"),
            version("aiohttp"),
        )
    username: str = entry.data.get("username")  # type: ignore
    password: str = entry.data.get("password")  # type: ignore
    update_interval = entry.options.get(OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    country = entry.options.get(
        OPTION_COUNTRY, entry.data.get(OPTION_COUNTRY, DEFAULT_COUNTRY)
    )
    brand = entry.options.get(OPTION_BRAND, entry.data.get(OPTION_BRAND, DEFAULT_BRAND))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "quota_time": None,
        "quota_exc_info": None,
    }

    _LOGGER.debug("Creating API and logging in with %s in realm %s", username, country)
    api = MyPyllantAPI(
        username=username, password=password, brand=brand, country=country
    )
    await api.login()

    system_coordinator = SystemCoordinator(
        hass, api, entry, timedelta(seconds=update_interval)
    )
    _LOGGER.debug("Refreshing SystemCoordinator")
    await system_coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id]["system_coordinator"] = system_coordinator

    # Daily data coordinator is updated hourly, but requests data for the whole day
    device_data_coordinator = DeviceDataCoordinator(
        hass, api, entry, timedelta(hours=1)
    )
    _LOGGER.debug("Refreshing DailyDataCoordinator")
    await device_data_coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id][
        "device_data_coordinator"
    ] = device_data_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Cleanup orphaned devices
    try:
        await async_remove_orphaned_devices(hass, entry)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Error in async_remove_orphaned_devices")

    async def handle_export(call: ServiceCall) -> ServiceResponse:
        return {
            "export": await export.main(
                user=username,
                password=password,
                brand=brand,
                country=country,
                data=call.data.get("data", False),
                resolution=call.data.get("resolution", DeviceDataBucketResolution.DAY),
                start=call.data.get("start"),
                end=call.data.get("end"),
            )
        }

    async def handle_generate_test_data(call: ServiceCall) -> ServiceResponse:
        return await generate_test_data.main(
            user=username,
            password=password,
            brand=brand,
            country=country,
            write_results=False,
        )

    async def handle_report(call: ServiceCall) -> ServiceResponse:
        return {
            f.file_name: f.file_content
            async for f in report.main(
                user=username,
                password=password,
                brand=brand,
                country=country,
                year=call.data.get("year"),
                write_results=False,
            )
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT,
        handle_export,
        schema=vol.Schema(
            {
                vol.Optional("data"): bool,
                vol.Optional("resolution"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_DEVICE_DATA_BUCKET_RESOLUTION_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    ),
                ),
                vol.Optional("start"): vol.Coerce(as_datetime),
                vol.Optional("end"): vol.Coerce(as_datetime),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_TEST_DATA,
        handle_generate_test_data,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPORT,
        handle_report,
        schema=vol.Schema(
            {
                vol.Required("year", default=dt.now().year): vol.Coerce(int),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id][
            "system_coordinator"
        ].api.aiohttp_session.close()
        await hass.data[DOMAIN][entry.entry_id][
            "device_data_coordinator"
        ].api.aiohttp_session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
