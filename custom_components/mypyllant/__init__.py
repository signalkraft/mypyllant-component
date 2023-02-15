from __future__ import annotations
from datetime import datetime, timedelta
from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES

from myPyllant.api import MyPyllantAPI
from myPyllant.models import System

import logging

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

    api = MyPyllantAPI(username, password)
    await api.login()
    coordinator = MyPyllantUpdateCoordinator(hass, api, entry)
    await coordinator.async_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id]["coordinator"].api.session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MyPyllantUpdateCoordinator(DataUpdateCoordinator):
    api: MyPyllantAPI
    data: List[System]

    def __init__(
        self,
        hass: HomeAssistant,
        api: MyPyllantAPI,
        entry: ConfigEntry,
    ) -> None:
        self.api = api
        self.hass = hass
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name="myVAILLANT",
            update_interval=MIN_TIME_BETWEEN_UPDATES,
        )

    async def _async_update_data(self):
        if self.api.session_expires < datetime.now() + timedelta(seconds=600):
            _LOGGER.warning(f"Refreshing session for {self.api.username}")
            await self.hass.async_add_executor_job(self.api.refresh_token)
        else:
            delta = self.api.session_expires - (datetime.now() + timedelta(seconds=600))
            _LOGGER.warning(
                f"Waiting {delta.seconds}s until refresh session for {self.api.username}"
            )
        data = [
            s
            async for s in await self.hass.async_add_executor_job(self.api.get_systems)
        ]
        return data
