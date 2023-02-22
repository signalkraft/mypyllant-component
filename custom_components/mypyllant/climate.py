from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from myPyllant.models import (
    System,
    Zone,
    ZoneCurrentSpecialFunction,
    ZoneHeatingOperatingMode,
)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_NONE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SystemCoordinator
from .const import DEFAULT_QUICK_VETO_DURATION, DOMAIN

_LOGGER = logging.getLogger(__name__)

HVAC_MODE_MAP = {
    HVACMode.OFF: ZoneHeatingOperatingMode.OFF,
    HVACMode.HEAT_COOL: ZoneHeatingOperatingMode.MANUAL,
    HVACMode.AUTO: ZoneHeatingOperatingMode.TIME_CONTROLLED,
}

PRESET_MAP = {
    PRESET_BOOST: ZoneCurrentSpecialFunction.QUICK_VETO,
    PRESET_NONE: ZoneCurrentSpecialFunction.NONE,
    PRESET_AWAY: ZoneCurrentSpecialFunction.HOLIDAY,
}


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]

    climates: list[ClimateEntity] = []

    for index, system in enumerate(coordinator.data):
        for zone_index, zone in enumerate(system.zones):
            climates.append(ZoneClimate(index, zone_index, coordinator))

    async_add_entities(climates)


class ZoneClimate(CoordinatorEntity, ClimateEntity):
    """Climate for a zone."""

    coordinator: SystemCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [str(k) for k in HVAC_MODE_MAP.keys()]
    _attr_preset_modes = [str(k) for k in PRESET_MAP.keys()]

    def __init__(
        self,
        system_index: int,
        zone_index: int,
        coordinator: SystemCoordinator,
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
            identifiers={(DOMAIN, f"zone{self.zone.index}")},
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
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def target_temperature(self) -> float:
        return self.zone.desired_room_temperature_setpoint

    @property
    def current_temperature(self) -> float:
        return self.zone.current_room_temperature

    @property
    def current_humidity(self) -> float:
        return self.zone.humidity

    @property
    def hvac_mode(self) -> HVACMode:
        return [
            k for k, v in HVAC_MODE_MAP.items() if v == self.zone.heating_operation_mode
        ][0]

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_zone_heating_operating_mode(
            self.zone,
            HVAC_MODE_MAP[hvac_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature and temperature != self.target_temperature:
            await self.coordinator.api.quick_veto_zone_temperature(
                self.zone, temperature, DEFAULT_QUICK_VETO_DURATION
            )
            await self.coordinator.async_request_refresh_delayed()

    @property
    def preset_mode(self) -> PRESET_BOOST | PRESET_NONE:
        return [
            k for k, v in PRESET_MAP.items() if v == self.zone.current_special_function
        ][0]

    async def async_set_preset_mode(self, preset_mode):
        requested_mode = PRESET_MAP[preset_mode]
        if requested_mode != self.zone.current_special_function:
            if requested_mode == ZoneCurrentSpecialFunction.NONE:
                if (
                    self.zone.current_special_function
                    == ZoneCurrentSpecialFunction.QUICK_VETO
                ):
                    # If quick veto is set, we cancel that
                    await self.coordinator.api.cancel_quick_veto_zone_temperature(
                        self.zone
                    )
                elif (
                    self.zone.current_special_function
                    == ZoneCurrentSpecialFunction.HOLIDAY
                ):
                    # If holiday mode is set, we cancel that instead
                    await self.coordinator.api.cancel_holiday(self.system)
            if requested_mode == ZoneCurrentSpecialFunction.QUICK_VETO:
                await self.coordinator.api.quick_veto_zone_temperature(
                    self.zone,
                    self.zone.manual_mode_setpoint,
                    DEFAULT_QUICK_VETO_DURATION,
                )
            if requested_mode == ZoneCurrentSpecialFunction.HOLIDAY:
                await self.coordinator.api.set_holiday(self.system)

            await self.coordinator.async_request_refresh_delayed()
