from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging

from myPyllant.api import MyPyllantAPI
from myPyllant.models import DeviceData, DeviceDataBucketResolution, System

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, OPTION_UPDATE_INTERVAL

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

    _LOGGER.debug(f"Creating API and logging in with {username}")
    api = MyPyllantAPI(username, password)
    await api.login()
    system_coordinator = SystemCoordinator(
        hass, api, entry, timedelta(seconds=update_interval)
    )
    _LOGGER.debug(f"Refreshing SystemCoordinator")
    await system_coordinator.async_refresh()
    data_coordinator = HistoricalDataCoordinator(hass, api, entry, timedelta(hours=1))
    _LOGGER.debug(f"Refreshing HistoricalDataCoordinator")
    await data_coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "system_coordinator": system_coordinator,
        "data_coordinator": data_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id][
            "system_coordinator"
        ].api.session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MyPyllantCoordinator(DataUpdateCoordinator):
    api: MyPyllantAPI
    data: list[System]

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

    async def _refresh_session(self):
        if self.api.oauth_session_expires < datetime.now() + timedelta(seconds=600):
            _LOGGER.debug(f"Refreshing token for {self.api.username}")
            await self.api.refresh_token()
        else:
            delta = self.api.oauth_session_expires - (
                datetime.now() + timedelta(seconds=600)
            )
            _LOGGER.debug(
                f"Waiting {delta.seconds}s until token refresh for {self.api.username}"
            )

    async def async_request_refresh_delayed(self):
        """
        The API takes a long time to return updated values (i.e. after setting a new heating mode)
        This function waits for a few second and then refreshes
        """
        await asyncio.sleep(4)
        await self.async_request_refresh()


class SystemCoordinator(MyPyllantCoordinator):
    data: list[System]

    async def _async_update_data(self) -> list[System]:
        _LOGGER.debug(f"Starting async update data for SystemCoordinator")
        await self._refresh_session()
        data = [
            s
            async for s in await self.hass.async_add_executor_job(self.api.get_systems)
        ]
        return data


class HistoricalDataCoordinator(MyPyllantCoordinator):
    data: list[list[DeviceData]]

    async def _async_update_data(self) -> list[list[DeviceData]]:
        _LOGGER.debug(f"Starting async update data for HistoricalDataCoordinator")
        await self._refresh_session()
        data = []
        start = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
        end = start + timedelta(days=1)
        _LOGGER.debug(f"Getting data from {start} to {end}")
        async for system in await self.hass.async_add_executor_job(
            self.api.get_systems
        ):
            async for device in self.api.get_devices_by_system(system):
                device_data = self.api.get_data_by_device(
                    device, DeviceDataBucketResolution.HOUR, start, end
                )
                data.append([da async for da in device_data])
        return data
