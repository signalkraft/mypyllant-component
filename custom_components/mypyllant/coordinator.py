from __future__ import annotations

import asyncio
import logging
from asyncio import CancelledError
from datetime import timedelta, datetime as dt, timezone
from typing import TypedDict

from aiohttp import ClientResponseError
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import get_last_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import entity_registry as er

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
    OPTION_FETCH_AMBISENSE_CAPABILITY,
    DEFAULT_FETCH_AMBISENSE_CAPABILITY,
    OPTION_FETCH_CONNECTION_STATUS,
    DEFAULT_FETCH_CONNECTION_STATUS,
    OPTION_FETCH_DTC,
    DEFAULT_FETCH_DTC,
    STATISTICS_BACKFILL_MAX_DAYS,
    STATISTICS_HOUR_REQUEST_MAX_DAYS,
)
from custom_components.mypyllant.utils import (
    is_quota_exceeded_exception,
    extract_quota_duration,
)
from myPyllant.api import AmbisenseNoFacilityError, MyPyllantAPI
from myPyllant.enums import DeviceDataBucketResolution
from myPyllant.models import System, DeviceData, Home

_LOGGER = logging.getLogger(__name__)


def local_midnight(value: dt, tz) -> dt:
    """Local midnight of value's date in tz, constructed from the date so it stays
    on midnight across DST transitions."""
    day = value.astimezone(tz).date()
    return dt(day.year, day.month, day.day, tzinfo=tz)


def backfill_ranges(start: dt, end: dt, max_days: int) -> list[tuple[dt, dt]]:
    """Split [start, end) into ranges the HOUR resolution of the API accepts."""
    ranges = []
    while start < end:
        range_end = min(start + timedelta(days=max_days), end)
        ranges.append((start, range_end))
        start = range_end
    return ranges


def merge_device_data(target: list[DeviceData], earlier: list[DeviceData]) -> None:
    """Merge buckets fetched for an earlier range into the matching DeviceData,
    keeping buckets sorted by start and the newer fetch's values on overlap."""
    for current, extra in zip(target, earlier):
        if (current.operation_mode, current.energy_type) != (
            extra.operation_mode,
            extra.energy_type,
        ):
            continue
        known = {bucket.start_date for bucket in current.data}
        current.data = sorted(
            [bucket for bucket in extra.data if bucket.start_date not in known]
            + list(current.data),
            key=lambda bucket: bucket.start_date,
        )


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
        self._quota_hit_time_key = f"quota_time_{self.__class__.__name__.lower()}"
        self._quota_end_time_key = f"quota_end_time_{self.__class__.__name__.lower()}"
        self._quota_exc_info_key = f"quota_exc_info_{self.__class__.__name__.lower()}"

        super().__init__(
            hass,
            _LOGGER,
            name="myVAILLANT",
            update_interval=update_interval,
        )

    @property
    def hass_data(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]

    @property
    def _quota_hit_time(self) -> dt | None:
        """
        Get the time when the quota was hit, separately for each subclass
        """
        if self._quota_hit_time_key not in self.hass_data:
            self.hass_data[self._quota_hit_time_key] = None
        return self.hass_data[self._quota_hit_time_key]

    @_quota_hit_time.setter
    def _quota_hit_time(self, value):
        self.hass_data[self._quota_hit_time_key] = value

    @_quota_hit_time.deleter
    def _quota_hit_time(self):
        del self.hass_data[self._quota_hit_time_key]

    @property
    def _quota_end_time(self) -> dt | None:
        """
        Get the time when the quota was hit, separately for each subclass
        """
        if self._quota_end_time_key not in self.hass_data:
            self.hass_data[self._quota_end_time_key] = None
        return self.hass_data[self._quota_end_time_key]

    @_quota_end_time.setter
    def _quota_end_time(self, value):
        self.hass_data[self._quota_end_time_key] = value

    @_quota_end_time.deleter
    def _quota_end_time(self):
        del self.hass_data[self._quota_end_time_key]

    @property
    def _quota_exc_info(self) -> BaseException | None:
        """
        Get the exception that happened when the quota was hit, separately for each subclass
        """
        if self._quota_exc_info_key not in self.hass_data:
            self.hass_data[self._quota_exc_info_key] = None
        return self.hass_data[self._quota_exc_info_key]

    @_quota_exc_info.setter
    def _quota_exc_info(self, value):
        self.hass_data[self._quota_exc_info_key] = value

    @_quota_exc_info.deleter
    def _quota_exc_info(self):
        del self.hass_data[self._quota_exc_info_key]

    def _clear_quota_state(self) -> None:
        """Clear all quota-related state to allow fresh retries."""
        self._quota_hit_time = None
        self._quota_end_time = None
        self._quota_exc_info = None

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
        self._quota_hit_time = dt.now(timezone.utc)
        self._quota_exc_info = exc_info
        raise UpdateFailed(
            f"myVAILLANT API is down, skipping update of myVAILLANT {self.__class__.__name__} "
            f"for another {QUOTA_PAUSE_INTERVAL}s"
        ) from exc_info

    def _set_quota_and_raise(self, exc_info: ClientResponseError) -> None:
        """
        Check if the API raises a ClientResponseError with "Quota Exceeded" in the message
        Raises UpdateFailed if a quota error is detected
        """
        if is_quota_exceeded_exception(exc_info):
            duration = extract_quota_duration(exc_info)
            self._quota_hit_time = dt.now(timezone.utc)
            if duration:
                self._quota_end_time = dt.now(timezone.utc) + timedelta(
                    seconds=duration
                )
            self._quota_exc_info = exc_info
            self._raise_if_quota_hit()

    def _raise_if_quota_hit(self) -> None:
        """
        Check if we previously hit a quota, and if the quota was hit within a certain interval
        If yes, we keep raising UpdateFailed() until after the interval to avoid spamming the API
        """
        if not self._quota_hit_time:
            return

        time_elapsed = (dt.now(timezone.utc) - self._quota_hit_time).total_seconds()

        if is_quota_exceeded_exception(self._quota_exc_info):
            _LOGGER.debug(
                "Quota was hit %ss ago on %s by %s",
                int(time_elapsed),
                self._quota_hit_time,
                self.__class__,
                exc_info=self._quota_exc_info,
            )
            if self._quota_end_time:
                # If the API responded with an end time, we use that instead of the default QUOTA_PAUSE_INTERVAL
                if dt.now(timezone.utc) < self._quota_end_time:
                    remaining = int(
                        (self._quota_end_time - dt.now(timezone.utc)).total_seconds()
                    )
                    raise UpdateFailed(
                        f"{self._quota_exc_info.message} on {self._quota_exc_info.request_info.real_url}, "  # type: ignore
                        f"skipping update of myVAILLANT {self.__class__.__name__} for another"
                        f" {remaining}s"
                    ) from self._quota_exc_info
                else:
                    # Quota backoff period has expired, clear state and allow retry
                    _LOGGER.info(
                        "Quota backoff expired for %s, clearing quota state and resuming updates",
                        self.__class__.__name__,
                    )
                    self._clear_quota_state()
                    return
            elif time_elapsed < QUOTA_PAUSE_INTERVAL:
                # No end time provided, use default interval
                raise UpdateFailed(
                    f"{self._quota_exc_info.message} on {self._quota_exc_info.request_info.real_url}, "  # type: ignore
                    f"skipping update of myVAILLANT {self.__class__.__name__} for another"
                    f" {int(QUOTA_PAUSE_INTERVAL - time_elapsed)}s"
                ) from self._quota_exc_info
            else:
                # Default backoff period has expired, clear state and allow retry
                _LOGGER.info(
                    "Quota backoff expired for %s (no end time), clearing quota state and resuming updates",
                    self.__class__.__name__,
                )
                self._clear_quota_state()
                return
        else:
            _LOGGER.debug(
                "myVAILLANT API is down since %ss (%s)",
                int(time_elapsed),
                self._quota_hit_time,
                exc_info=self._quota_exc_info,
            )
            if time_elapsed < API_DOWN_PAUSE_INTERVAL:
                raise UpdateFailed(
                    f"myVAILLANT API is down, skipping update of myVAILLANT {self.__class__.__name__} for another"
                    f" {int(API_DOWN_PAUSE_INTERVAL - time_elapsed)}s"
                ) from self._quota_exc_info
            else:
                # API down backoff has expired, clear state and allow retry
                _LOGGER.info(
                    "API down backoff expired for %s, clearing state and resuming updates",
                    self.__class__.__name__,
                )
                self._clear_quota_state()
                return


class SystemCoordinator(MyPyllantCoordinator):
    data: list[System]  # type: ignore
    homes: list[Home] = []

    async def _async_update_data(self) -> list[System]:  # type: ignore
        self._raise_if_quota_hit()
        include_connection_status = self.entry.options.get(
            OPTION_FETCH_CONNECTION_STATUS, DEFAULT_FETCH_CONNECTION_STATUS
        )
        include_diagnostic_trouble_codes = self.entry.options.get(
            OPTION_FETCH_DTC, DEFAULT_FETCH_DTC
        )
        include_rts = self.entry.options.get(OPTION_FETCH_RTS, DEFAULT_FETCH_RTS)
        include_mpc = self.entry.options.get(OPTION_FETCH_MPC, DEFAULT_FETCH_MPC)
        include_ambisense_rooms = self.entry.options.get(
            OPTION_FETCH_AMBISENSE_ROOMS, DEFAULT_FETCH_AMBISENSE_ROOMS
        )
        include_energy_management = self.entry.options.get(
            OPTION_FETCH_ENERGY_MANAGEMENT, DEFAULT_FETCH_ENERGY_MANAGEMENT
        )
        include_eebus = self.entry.options.get(OPTION_FETCH_EEBUS, DEFAULT_FETCH_EEBUS)
        include_ambisense_capability = self.entry.options.get(
            OPTION_FETCH_AMBISENSE_CAPABILITY, DEFAULT_FETCH_AMBISENSE_CAPABILITY
        )
        _LOGGER.debug("Starting async update data for SystemCoordinator")
        try:
            await self._refresh_session()
            if not self.homes:
                _LOGGER.debug("Fetching homes for systems fetch")
                self.homes = [
                    h
                    async for h in await self.hass.async_add_executor_job(
                        self.api.get_homes
                    )
                ]
            else:
                _LOGGER.debug("Using cached homes for systems fetch")
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
                    include_ambisense_capability,
                    self.homes,
                )
            ]
            # Clear quota state on successful fetch so future updates aren't blocked
            self._clear_quota_state()
            return data
        except AmbisenseNoFacilityError as e:
            _LOGGER.warning(
                "Ambisense rooms not available for one or more systems, "
                "consider disabling the Ambisense rooms option: %s",
                e,
            )
            return []
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

    async def is_sensor_disabled(self, unique_id: str) -> bool:
        """
        Check if a sensor is disabled to be able to skip its API update
        """
        entity_registry = er.async_get(self.hass)
        entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id:
            entity_entry = entity_registry.async_get(entity_id)
            return entity_entry is not None and bool(entity_entry.disabled)
        return False

    async def statistics_gap_start(
        self, device, de_index: int, start: dt, tz
    ) -> dt | None:
        """
        Start of hourly data that has not been published as statistics yet

        The regular fetch only covers yesterday + today, so hours missed while
        updates failed for longer (quota pause, API outage, HA downtime) would
        never be published. Returns local midnight of the oldest "last published
        statistic" across the device's enabled data sensors if it lies before
        `start`, capped at STATISTICS_BACKFILL_MAX_DAYS. Series that never
        published anything are ignored, so a fresh install does not backfill.
        """
        if "recorder" not in self.hass.config.components:
            return None
        oldest: float | None = None
        for da_index, device_data in enumerate(device.data):
            if device_data.skip_data_update:
                continue
            sensor_id = f"{DOMAIN}_{device.system_id}_{device.device_uuid}_{da_index}_{de_index}"
            statistic_id = f"{DOMAIN}:{sensor_id}".lower().replace("-", "_")
            last_stats = await get_instance(self.hass).async_add_executor_job(
                get_last_statistics, self.hass, 1, statistic_id, False, {"sum"}
            )
            rows = last_stats.get(statistic_id)
            if rows and (oldest is None or rows[0]["start"] < oldest):
                oldest = rows[0]["start"]
        if oldest is None:
            return None
        gap_start = max(
            local_midnight(dt.fromtimestamp(oldest, tz), tz),
            local_midnight(start - timedelta(days=STATISTICS_BACKFILL_MAX_DAYS), tz),
        )
        return gap_start if gap_start < start else None

    async def _async_update_data(self) -> dict[str, SystemWithDeviceData]:
        self._raise_if_quota_hit()
        _LOGGER.debug("Starting async update data for DailyDataCoordinator")
        try:
            await self._refresh_session()
            data: dict[str, SystemWithDeviceData] = {}
            if (
                "system_coordinator" not in self.hass_data
                or not self.hass_data["system_coordinator"].data
            ):
                raise UpdateFailed("No systems available for daily data fetch")
            for system in self.hass_data["system_coordinator"].data:
                today = dt.now(system.timezone).replace(
                    microsecond=0, second=0, minute=0, hour=0
                )
                # Fetch yesterday + today so the previous day's final hour (23:00-00:00)
                # is backfilled once it finalises after midnight. Date-based construction
                # keeps the start on local midnight across DST transitions (a raw
                # `today - timedelta(days=1)` is off by an hour on DST-change days).
                yesterday = (today - timedelta(days=1)).date()
                start = dt(
                    yesterday.year,
                    yesterday.month,
                    yesterday.day,
                    tzinfo=system.timezone,
                )
                end = today + timedelta(days=1)
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
                for de_index, device in enumerate(system.devices):
                    for da_index, dd in enumerate(device.data):
                        sensor_id = f"{DOMAIN}_{device.system_id}_{device.device_uuid}_{da_index}_{de_index}"
                        if await self.is_sensor_disabled(sensor_id):
                            device.data[da_index].skip_data_update = True
                    device_data = [
                        da
                        async for da in self.api.get_data_by_device(
                            device, DeviceDataBucketResolution.HOUR, start, end
                        )
                    ]
                    gap_start = await self.statistics_gap_start(
                        device, de_index, start, system.timezone
                    )
                    if gap_start is not None:
                        _LOGGER.debug(
                            "Backfilling hourly data for %s from %s to %s",
                            device.device_uuid,
                            gap_start,
                            start,
                        )
                        for range_start, range_end in backfill_ranges(
                            gap_start, start, STATISTICS_HOUR_REQUEST_MAX_DAYS
                        ):
                            merge_device_data(
                                device_data,
                                [
                                    da
                                    async for da in self.api.get_data_by_device(
                                        device,
                                        DeviceDataBucketResolution.HOUR,
                                        range_start,
                                        range_end,
                                    )
                                ],
                            )
                    data[system.id]["devices_data"].append(device_data)
            # Clear quota state on successful fetch so future updates aren't blocked
            self._clear_quota_state()
            return data
        except ClientResponseError as e:
            self._set_quota_and_raise(e)
            raise UpdateFailed(str(e)) from e
        except (CancelledError, TimeoutError) as e:
            self._raise_api_down(e)
            return {}  # mypy
