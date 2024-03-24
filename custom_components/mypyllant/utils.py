from __future__ import annotations

import logging
import typing
from asyncio.exceptions import CancelledError
from collections.abc import MutableSequence
from datetime import datetime, timedelta
from typing import TypeVar

from aiohttp.client_exceptions import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from custom_components.mypyllant.const import DOMAIN, OPTION_DEFAULT_HOLIDAY_DURATION
from myPyllant.const import DEFAULT_HOLIDAY_DURATION

if typing.TYPE_CHECKING:
    from custom_components.mypyllant.coordinator import SystemCoordinator
    from myPyllant.models import System, DomesticHotWater, Zone, AmbisenseRoom

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class EntityList(MutableSequence[_T | typing.Callable[[], _T]]):
    """
    A list that takes a callable for the item value, calls it, and logs exceptions without raising them
    When adding multiple entities in a setup function, an error on one entity
    doesn't prevent the others from being added
    """

    def __init__(self, *args):
        self.list = list()
        self.extend(list(args))

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, value):
        value, raised = self.call_and_log(value)
        if not raised:
            self.list[i] = value
        else:
            del self.list[i]

    def call_and_log(self, value):
        if callable(value):
            try:
                return value(), False
            except Exception as e:
                logger.error(f"Error initializing entity: {e}", exc_info=e)
                return None, True
        else:
            return value, False

    def append(self, value):
        value, raised = self.call_and_log(value)
        if not raised:
            self.list.append(value)

    def insert(self, i, value):
        value, raised = self.call_and_log(value)
        if not raised:
            self.list.insert(i, self.call_and_log(value))

    def __str__(self):
        return str(self.list)


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
    def __init__(
        self,
        index: int,
        coordinator: "SystemCoordinator",
        config: ConfigEntry,
    ) -> None:
        super().__init__(index, coordinator)
        self.config = config

    @property
    def default_holiday_duration(self):
        return self.config.options.get(
            OPTION_DEFAULT_HOLIDAY_DURATION, DEFAULT_HOLIDAY_DURATION
        )

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


class ZoneCoordinatorEntity(CoordinatorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, zone_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def zone(self) -> Zone:
        return self.system.zones[self.zone_index]

    @property
    def circuit_name_suffix(self) -> str:
        if self.zone.associated_circuit_index is None:
            return ""
        else:
            return f" (Circuit {self.zone.associated_circuit_index})"

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} Zone {shorten_zone_name(self.zone.name)}{self.circuit_name_suffix}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_zone_{self.zone.index}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )

    @property
    def available(self) -> bool | None:
        return self.zone.is_active


class AmbisenseCoordinatorEntity(CoordinatorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self,
        system_index: int,
        room_index: int,
        coordinator: SystemCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.room_index = room_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def room(self) -> AmbisenseRoom:
        return [
            r for r in self.system.ambisense_rooms if r.room_index == self.room_index
        ][0]

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} {self.room.name}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_room_{self.room_index}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_climate"
