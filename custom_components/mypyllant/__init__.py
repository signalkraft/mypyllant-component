from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from aiohttp.client_exceptions import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from myPyllant.api import MyPyllantAPI
from myPyllant.const import DEFAULT_BRAND
from myPyllant.models import DeviceData, DeviceDataBucketResolution, System

from .const import (
    DEFAULT_COUNTRY,
    DEFAULT_REFRESH_DELAY,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPTION_BRAND,
    OPTION_COUNTRY,
    OPTION_REFRESH_DELAY,
    OPTION_UPDATE_INTERVAL,
    QUOTA_PAUSE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    username = entry.data.get("username")
    password = entry.data.get("password")
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
        update_interval: timedelta,
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

    def _set_quota(self, e: ClientResponseError) -> None:
        """
        Check if the API returns an error with "Quota Exceeded" in the message
        """
        if e.status == 403 and "quota exceeded" in e.message.lower():
            self.hass.data[DOMAIN][self.entry.entry_id]["quota_time"] = datetime.now()
            self.hass.data[DOMAIN][self.entry.entry_id]["quota_exc_info"] = e
            self._raise_if_quota_hit()

    def _raise_if_quota_hit(self) -> None:
        """
        Check if we previously hit a quota, and if the quota was hit within a certain interval
        If yes, we keep raising UpdateFailed() until after the interval to avoid spamming the API
        """
        quota_time = self.hass.data[DOMAIN][self.entry.entry_id]["quota_time"]
        if not quota_time:
            return

        time_elapsed = (datetime.now() - quota_time).seconds
        _LOGGER.debug("Quota was hit %ss ago on %s", time_elapsed, quota_time)
        if time_elapsed < QUOTA_PAUSE_INTERVAL:
            exc_info: ClientResponseError = self.hass.data[DOMAIN][self.entry.entry_id][
                "quota_exc_info"
            ]
            raise UpdateFailed(
                f"{exc_info.message} on {exc_info.request_info.real_url}, "
                f"skipping update of myVAILLANT data for another {QUOTA_PAUSE_INTERVAL - time_elapsed}s",
            ) from exc_info

    async def _refresh_session(self):
        if self.api.oauth_session_expires < datetime.now() + timedelta(seconds=180):
            _LOGGER.debug("Refreshing token for %s", self.api.username)
            await self.api.refresh_token()
        else:
            delta = self.api.oauth_session_expires - (
                datetime.now() + timedelta(seconds=180)
            )
            _LOGGER.debug(
                "Waiting %ss until token refresh for %s",
                delta.seconds,
                self.api.username,
            )

    async def async_request_refresh_delayed(self):
        """
        The API takes a long time to return updated values (i.e. after setting a new heating mode)
        This function waits for a few second and then refreshes
        """
        delay = self.entry.options.get(OPTION_REFRESH_DELAY, DEFAULT_REFRESH_DELAY)
        await asyncio.sleep(delay)
        await self.async_request_refresh()


class SystemCoordinator(MyPyllantCoordinator):
    data: list[System]

    async def _async_update_data(self) -> list[System] | None:
        self._raise_if_quota_hit()
        _LOGGER.debug("Starting async update data for SystemCoordinator")
        try:
            await self._refresh_session()
            data = [
                s
                async for s in await self.hass.async_add_executor_job(
                    self.api.get_systems, True, True, True
                )
            ]
            return data
        except ClientResponseError as e:
            self._set_quota(e)
            return None


class DailyDataCoordinator(MyPyllantCoordinator):
    data: dict[str, list[DeviceData]]

    async def _async_update_data(self) -> dict[str, list[DeviceData]] | None:
        self._raise_if_quota_hit()
        _LOGGER.debug("Starting async update data for DailyDataCoordinator")
        try:
            await self._refresh_session()
            data: dict[str, list[DeviceData]] = {}
            start = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
            end = start + timedelta(days=1)
            _LOGGER.debug("Getting data from %s to %s", start, end)
            async for system in await self.hass.async_add_executor_job(
                self.api.get_systems
            ):
                data[system.id] = []
                for device in system.devices:
                    device_data = self.api.get_data_by_device(
                        device, DeviceDataBucketResolution.DAY, start, end
                    )
                    data[system.id] += [da async for da in device_data]
            return data
        except ClientResponseError as e:
            self._set_quota(e)
            return None
