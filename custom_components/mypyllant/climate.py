from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, List

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import MyPyllantUpdateCoordinator
from .const import DOMAIN, DEFAULT_QUICK_VETO_DURATION
from myPyllant.models import System, Zone


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: MyPyllantUpdateCoordinator = hass.data[DOMAIN][config.entry_id][
        "coordinator"
    ]

    climates: List[ClimateEntity] = []

    for index, system in enumerate(coordinator.data):
        for zone_index, zone in enumerate(system.zones):
            climates.append(ZoneClimate(index, zone_index, coordinator))

    async_add_entities(climates)


class ZoneClimate(CoordinatorEntity, ClimateEntity):
    """Climate for a zone."""

    coordinator: MyPyllantUpdateCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_mode = HVACMode.AUTO
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.OFF]

    def __init__(
        self,
        system_index: int,
        zone_index: int,
        coordinator: MyPyllantUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index
        self.entity_id = f"{DOMAIN}.zone_{zone_index}"

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def zone(self) -> Zone:
        return self.system.zones[self.zone_index]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "zone", str(self.zone.index))},
            name=self.zone.name,
            manufacturer="Vaillant",
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_climate_zone_{self.zone_index}"

    @property
    def name(self) -> str:
        return self.zone.name

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {"time_windows": self.zone.time_windows}
        return attr

    async def set_quick_veto(self, **kwargs):
        temperature = kwargs.get("temperature")
        duration = kwargs.get("duration", DEFAULT_QUICK_VETO_DURATION)
        await self.coordinator.api.quick_veto_zone_temperature(
            self.zone, temperature, duration
        )

    async def remove_quick_veto(self, **kwargs):
        await self.coordinator.api.cancel_quick_veto_zone_temperature(self.zone)

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def target_temperature(self) -> float:
        return self.zone.desired_room_temperature_setpoint

    @property
    def current_temperature(self) -> float:
        return self.zone.current_room_temperature

    @property
    def current_humidity(self) -> float:
        return self.zone.humidity

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature and temperature != self.target_temperature:
            await self.coordinator.api.quick_veto_zone_temperature(
                self.zone, temperature, DEFAULT_QUICK_VETO_DURATION
            )
