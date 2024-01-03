from __future__ import annotations

import asyncio
import logging
from asyncio.exceptions import CancelledError
from datetime import datetime as dt, timedelta, timezone
from typing import TypedDict
import voluptuous as vol
from aiohttp.client_exceptions import ClientResponseError
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

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from myPyllant import export, report

from myPyllant.api import MyPyllantAPI
from myPyllant.const import DEFAULT_BRAND
from myPyllant.models import DeviceData, DeviceDataBucketResolution, System
from myPyllant.tests import generate_test_data
from .const import (
    API_DOWN_PAUSE_INTERVAL,
    DEFAULT_COUNTRY,
    DEFAULT_REFRESH_DELAY,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_REFRESH_DELAY,
    OPTION_UPDATE_INTERVAL,
    QUOTA_PAUSE_INTERVAL,
    SERVICE_GENERATE_TEST_DATA,
    SERVICE_EXPORT,
    SERVICE_REPORT,
)
from .utils import is_quota_exceeded_exception

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
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
        from homeassistant.helpers.entity_registry import async_migrate_entries, RegistryEntry
        from homeassistant.helpers.device_registry import async_entries_for_config_entry
        from homeassistant.core import callback

        devices = async_entries_for_config_entry(
            hass.data["device_registry"], config_entry.entry_id
        )

        @callback
        def update_unique_id(entity_entry: RegistryEntry):
            return {"new_unique_id": entity_entry.unique_id} # change entity_entry.unique_id

        await async_migrate_entries(hass, config_entry.entry_id, update_unique_id)
        config_entry.version = 2 # set to new version
        """

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
    daily_data_coordinator = DailyDataCoordinator(hass, api, entry, timedelta(hours=1))
    _LOGGER.debug("Refreshing DailyDataCoordinator")
    await daily_data_coordinator.async_refresh()
    hass.data[DOMAIN][entry.entry_id]["daily_data_coordinator"] = daily_data_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
            "daily_data_coordinator"
        ].api.aiohttp_session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MyPyllantCoordinator(DataUpdateCoordinator):
    api: MyPyllantAPI

    def __init__(
        self,
        hass: HomeAssistant,
        api: MyPyllantAPI,
        entry: ConfigEntry,
        update_interval: timedelta | None,
    ) -> None:
        self.api = api
        self.hass = hass
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name="myVAILLANT",
            update_interval=update_interval,
        )

    @property
    def hass_data(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]

    async def _refresh_session(self):
        if (
            self.api.oauth_session_expires is None
            or self.api.oauth_session_expires
            < dt.now(timezone.utc) + timedelta(seconds=180)
        ):
            _LOGGER.debug("Refreshing token for %s", self.api.username)
            await self.api.refresh_token()
        else:
            delta = self.api.oauth_session_expires - (
                dt.now(timezone.utc) + timedelta(seconds=180)
            )
            _LOGGER.debug(
                "Waiting %ss until token refresh for %s",
                delta.seconds,
                self.api.username,
            )

    async def async_request_refresh_delayed(self, delay=None):
        """
        The API takes a long time to return updated values (i.e. after setting a new heating mode)
        This function waits for a few second and then refreshes
        """
        if not delay:
            delay = self.entry.options.get(OPTION_REFRESH_DELAY, DEFAULT_REFRESH_DELAY)
        if delay:
            await asyncio.sleep(delay)
        await self.async_request_refresh()

    def _raise_api_down(self, exc_info: CancelledError | TimeoutError) -> None:
        """
        Raises UpdateFailed if a TimeoutError or CancelledError occurred during updating

        Sets a quota time, so the API isn't queried as often while it is down
        """
        self.hass_data["quota_time"] = dt.now()
        self.hass_data["quota_exc_info"] = exc_info
        raise UpdateFailed(
            f"myVAILLANT API is down, skipping update of myVAILLANT data for another {QUOTA_PAUSE_INTERVAL}s"
        ) from exc_info

    def _set_quota_and_raise(self, exc_info: ClientResponseError) -> None:
        """
        Check if the API raises a ClientResponseError with "Quota Exceeded" in the message
        Raises UpdateFailed if a quota error is detected
        """
        if is_quota_exceeded_exception(exc_info):
            self.hass_data["quota_time"] = dt.now()
            self.hass_data["quota_exc_info"] = exc_info
            self._raise_if_quota_hit()

    def _raise_if_quota_hit(self) -> None:
        """
        Check if we previously hit a quota, and if the quota was hit within a certain interval
        If yes, we keep raising UpdateFailed() until after the interval to avoid spamming the API
        """
        quota_time: dt = self.hass_data["quota_time"]
        if not quota_time:
            return

        time_elapsed = (dt.now() - quota_time).seconds
        exc_info: Exception = self.hass_data["quota_exc_info"]

        if is_quota_exceeded_exception(exc_info):
            _LOGGER.debug(
                "Quota was hit %ss ago on %s",
                time_elapsed,
                quota_time,
                exc_info=exc_info,
            )
            if time_elapsed < QUOTA_PAUSE_INTERVAL:
                raise UpdateFailed(
                    f"{exc_info.message} on {exc_info.request_info.real_url}, "  # type: ignore
                    f"skipping update of myVAILLANT data for another {QUOTA_PAUSE_INTERVAL - time_elapsed}s"
                ) from exc_info
        else:
            _LOGGER.debug(
                "myVAILLANT API is down since %ss (%s)",
                time_elapsed,
                quota_time,
                exc_info=exc_info,
            )
            if time_elapsed < API_DOWN_PAUSE_INTERVAL:
                raise UpdateFailed(
                    f"myVAILLANT API is down, skipping update of myVAILLANT data for another"
                    f" {API_DOWN_PAUSE_INTERVAL - time_elapsed}s"
                ) from exc_info


class SystemCoordinator(MyPyllantCoordinator):
    data: list[System]

    async def _async_update_data(self) -> list[System]:
        self._raise_if_quota_hit()
        _LOGGER.debug("Starting async update data for SystemCoordinator")
        try:
            await self._refresh_session()
            data = [
                s
                async for s in await self.hass.async_add_executor_job(
                    self.api.get_systems, True, True
                )
            ]
            return data
        except ClientResponseError as e:
            self._set_quota_and_raise(e)
            raise UpdateFailed() from e
        except (CancelledError, TimeoutError) as e:
            self._raise_api_down(e)
            return []  # mypy


class SystemWithDeviceData(TypedDict):
    home_name: str
    devices_data: list[list[DeviceData]]


class DailyDataCoordinator(MyPyllantCoordinator):
    data: dict[str, SystemWithDeviceData]

    async def _async_update_data(self) -> dict[str, SystemWithDeviceData]:
        self._raise_if_quota_hit()
        _LOGGER.debug("Starting async update data for DailyDataCoordinator")
        try:
            await self._refresh_session()
            data: dict[str, SystemWithDeviceData] = {}
            start = dt.now().replace(microsecond=0, second=0, minute=0, hour=0)
            end = start + timedelta(days=1)
            _LOGGER.debug("Getting data from %s to %s", start, end)
            async for system in await self.hass.async_add_executor_job(
                self.api.get_systems
            ):
                if len(system.devices) == 0:
                    continue
                data[system.id] = {
                    "home_name": system.home.home_name or system.home.nomenclature,
                    "devices_data": [],
                }
                for device in system.devices:
                    device_data = self.api.get_data_by_device(
                        device, DeviceDataBucketResolution.DAY, start, end
                    )
                    data[system.id]["devices_data"].append(
                        [da async for da in device_data]
                    )
            return data
        except ClientResponseError as e:
            self._set_quota_and_raise(e)
            raise UpdateFailed() from e
        except (CancelledError, TimeoutError) as e:
            self._raise_api_down(e)
            return {}  # mypy
