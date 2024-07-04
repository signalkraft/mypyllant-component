from __future__ import annotations

import asyncio
import logging
from asyncio import CancelledError
from datetime import timedelta, datetime as dt, timezone
from typing import TypedDict

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.mypyllant.const import (
    DOMAIN,
    OPTION_REFRESH_DELAY,
    DEFAULT_REFRESH_DELAY,
    QUOTA_PAUSE_INTERVAL,
    API_DOWN_PAUSE_INTERVAL,
    OPTION_FETCH_MPC,
    OPTION_FETCH_RTS,
    DEFAULT_FETCH_RTS,
    DEFAULT_FETCH_MPC,
    OPTION_FETCH_AMBISENSE_ROOMS,
    DEFAULT_FETCH_AMBISENSE_ROOMS,
    OPTION_FETCH_ENERGY_MANAGEMENT,
    DEFAULT_FETCH_ENERGY_MANAGEMENT,
    OPTION_FETCH_EEBUS,
    DEFAULT_FETCH_EEBUS,
)
from custom_components.mypyllant.utils import is_quota_exceeded_exception
from myPyllant.api import MyPyllantAPI
from myPyllant.enums import DeviceDataBucketResolution
from myPyllant.models import System, DeviceData

_LOGGER = logging.getLogger(__name__)


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

        # API calls sometimes update the models, so we update the data before waiting for the refresh
        # to see immediate changes in the UI
        self.async_set_updated_data(self.data)
        if not delay:
            delay = self.entry.options.get(OPTION_REFRESH_DELAY, DEFAULT_REFRESH_DELAY)
        if delay:
            _LOGGER.debug("Waiting %ss before refreshing data", delay)
            await asyncio.sleep(delay)
        await self.async_request_refresh()

    def _raise_api_down(self, exc_info: CancelledError | TimeoutError) -> None:
        """
        Raises UpdateFailed if a TimeoutError or CancelledError occurred during updating

        Sets a quota time, so the API isn't queried as often while it is down
        """
        self.hass_data["quota_time"] = dt.now(timezone.utc)
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
            self.hass_data["quota_time"] = dt.now(timezone.utc)
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

        time_elapsed = (dt.now(timezone.utc) - quota_time).seconds
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
    data: list[System]  # type: ignore

    async def _async_update_data(self) -> list[System]:  # type: ignore
        self._raise_if_quota_hit()
        include_connection_status = True
        include_diagnostic_trouble_codes = True
        include_rts = self.entry.options.get(OPTION_FETCH_RTS, DEFAULT_FETCH_RTS)
        include_mpc = self.entry.options.get(OPTION_FETCH_MPC, DEFAULT_FETCH_MPC)
        include_ambisense_rooms = self.entry.options.get(
            OPTION_FETCH_AMBISENSE_ROOMS, DEFAULT_FETCH_AMBISENSE_ROOMS
        )
        include_energy_management = self.entry.options.get(
            OPTION_FETCH_ENERGY_MANAGEMENT, DEFAULT_FETCH_ENERGY_MANAGEMENT
        )
        include_eebus = self.entry.options.get(OPTION_FETCH_EEBUS, DEFAULT_FETCH_EEBUS)
        _LOGGER.debug("Starting async update data for SystemCoordinator")
        try:
            await self._refresh_session()
            data = [
                s
                async for s in await self.hass.async_add_executor_job(
                    self.api.get_systems,
                    include_connection_status,
                    include_diagnostic_trouble_codes,
                    include_rts,
                    include_mpc,
                    include_ambisense_rooms,
                    include_energy_management,
                    include_eebus,
                )
            ]
            return data
        except ClientResponseError as e:
            self._set_quota_and_raise(e)
            raise UpdateFailed(str(e)) from e
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
            async for system in await self.hass.async_add_executor_job(
                self.api.get_systems
            ):
                start = dt.now(system.timezone).replace(
                    microsecond=0, second=0, minute=0, hour=0
                )
                end = start + timedelta(days=1)
                _LOGGER.debug(
                    "Getting daily data for %s from %s to %s", system.id, start, end
                )
                if len(system.devices) == 0:
                    _LOGGER.debug("No devices in %s", system.id)
                    continue
                data[system.id] = {
                    "home_name": system.home.home_name or system.home.nomenclature,
                    "devices_data": [],
                }
                for device in system.devices:
                    device_data = self.api.get_data_by_device(
                        device, DeviceDataBucketResolution.HOUR, start, end
                    )
                    data[system.id]["devices_data"].append(
                        [da async for da in device_data]
                    )
            return data
        except ClientResponseError as e:
            self._set_quota_and_raise(e)
            raise UpdateFailed(str(e)) from e
        except (CancelledError, TimeoutError) as e:
            self._raise_api_down(e)
            return {}  # mypy
