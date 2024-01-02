from __future__ import annotations

import logging
import typing
from asyncio.exceptions import CancelledError
from datetime import datetime, timedelta

from aiohttp.client_exceptions import ClientResponseError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from custom_components.mypyllant.const import DOMAIN

if typing.TYPE_CHECKING:
    from custom_components.mypyllant import SystemCoordinator
    from myPyllant.models import System, DomesticHotWater

logger = logging.getLogger(__name__)


class SystemCoordinatorEntity(CoordinatorEntity):
    coordinator: "SystemCoordinator"

    def __init__(self, index: int, coordinator: "SystemCoordinator") -> None:
        super().__init__(coordinator)
        self.index = index

    @property
    def system(self) -> "System":
        return self.coordinator.data[self.index]

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_home"

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature}"

    @property
    def device_info(self) -> DeviceInfo | None:
        return {"identifiers": {(DOMAIN, self.id_infix)}}


class HolidayEntity(SystemCoordinatorEntity):
    default_holiday_duration: int

    def __init__(
        self,
        index: int,
        coordinator: "SystemCoordinator",
        default_holiday_duration: int,
    ) -> None:
        super().__init__(index, coordinator)
        logging.debug(
            "Initializing %s with default holiday duration %s",
            self.__class__.__name__,
            default_holiday_duration,
        )
        self.default_holiday_duration = default_holiday_duration

    @property
    def extra_state_attributes(self) -> typing.Mapping[str, typing.Any] | None:
        return {
            "holiday_ongoing": self.zone.general.holiday_ongoing
            if self.zone
            else False,
            "holiday_remaining_seconds": self.zone.general.holiday_remaining.total_seconds()
            if self.zone.general.holiday_remaining
            else None,
            "holiday_start_date_time": self.holiday_start,
            "holiday_end_date_time": self.holiday_end,
        }

    @property
    def zone(self):
        return self.system.zones[0] if self.system.zones else None

    @property
    def holiday_start(self) -> datetime | None:
        return (
            self.zone.general.holiday_start_date_time
            if self.zone and self.zone.general.holiday_planned
            else None
        )

    @property
    def holiday_end(self) -> datetime | None:
        return (
            self.zone.general.holiday_end_date_time
            if self.zone and self.zone.general.holiday_planned
            else None
        )

    @property
    def holiday_remaining(self) -> timedelta | None:
        return self.zone.general.holiday_remaining if self.zone else None


def shorten_zone_name(zone_name: str) -> str:
    if zone_name.startswith("Zone "):
        return zone_name[5:]
    return zone_name


def is_quota_exceeded_exception(exc_info: Exception) -> bool:
    """
    Returns True if the exception is a quota exceeded ClientResponseError
    """
    return (
        isinstance(exc_info, ClientResponseError)
        and exc_info.status == 403
        and "quota exceeded" in exc_info.message.lower()
    )


def is_api_down_exception(exc_info: Exception) -> bool:
    """
    Returns True if the exception indicates that the myVAILLANT API is down
    """
    return isinstance(exc_info, CancelledError) or isinstance(exc_info, TimeoutError)


class DomesticHotWaterCoordinatorEntity(CoordinatorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, dhw_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.dhw_index = dhw_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} Domestic Hot Water {self.dhw_index}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_domestic_hot_water_{self.dhw_index}"

    @property
    def domestic_hot_water(self) -> DomesticHotWater:
        return self.system.domestic_hot_water[self.dhw_index]

    @property
    def device_info(self):
        return {
            "identifiers": {
                (
                    DOMAIN,
                    self.id_infix,
                )
            }
        }
