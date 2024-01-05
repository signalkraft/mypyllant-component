from __future__ import annotations
from abc import ABC

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.number import NumberEntity

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_NONE,
    PRESET_SLEEP,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature, UnitOfTime

from myPyllant.const import (
    DEFAULT_MANUAL_SETPOINT_TYPE,
    DEFAULT_QUICK_VETO_DURATION,
)
from myPyllant.models import (
    System,
    Zone,
    ZoneCurrentSpecialFunction,
    ZoneHeatingOperatingMode,
    ZoneTimeProgram,
)
from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.entities.base import (
    BaseHumidityEntity,
    BaseSystemCoordinator,
    BaseTemperatureEntity,
)

from custom_components.mypyllant.const import (
    DEFAULT_TIME_PROGRAM_OVERWRITE,
    OPTION_DEFAULT_QUICK_VETO_DURATION,
    OPTION_TIME_PROGRAM_OVERWRITE,
)

from homeassistant.config_entries import ConfigEntry


_LOGGER = logging.getLogger(__name__)


ZONE_HVAC_MODE_MAP = {
    HVACMode.OFF: ZoneHeatingOperatingMode.OFF,
    HVACMode.HEAT_COOL: ZoneHeatingOperatingMode.MANUAL,
    HVACMode.AUTO: ZoneHeatingOperatingMode.TIME_CONTROLLED,
}

ZONE_PRESET_MAP = {
    PRESET_BOOST: ZoneCurrentSpecialFunction.QUICK_VETO,
    PRESET_NONE: ZoneCurrentSpecialFunction.NONE,
    PRESET_AWAY: ZoneCurrentSpecialFunction.HOLIDAY,
    PRESET_SLEEP: ZoneCurrentSpecialFunction.SYSTEM_OFF,
}


def circuit_name_suffix(zone: Zone) -> str:
    if zone.associated_circuit_index is None:
        return ""
    else:
        return f" (Circuit {zone.associated_circuit_index})"


def shorten_zone_name(zone_name: str) -> str:
    if zone_name.startswith("Zone "):
        return zone_name[5:]
    return zone_name


def zone_device_name(system: System, zone: Zone):
    return f"Zone {shorten_zone_name(zone.name)}{circuit_name_suffix(zone)}"


class BaseZone(BaseSystemCoordinator, ABC):
    def __init__(
        self, system_index: int, zone_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(system_index, coordinator)
        self.zone_index = zone_index

    @property
    def zone(self) -> Zone:
        return self.system.zones[self.zone_index]

    @property
    def available(self) -> bool:
        return self.zone.is_active

    @property
    def name_prefix(self) -> str:
        return f"{super().name_prefix} {zone_device_name(self.system, self.zone)}"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_zone_{self.zone.index}"


class ZoneDesiredRoomTemperatureSetpointSensor(BaseZone, BaseTemperatureEntity):
    @property
    def name_suffix(self):
        return "Desired Temperature"

    @property
    def id_suffix(self) -> str:
        return "desired_temperature"

    @property
    def native_value(self):
        if self.zone.desired_room_temperature_setpoint_heating:
            return self.zone.desired_room_temperature_setpoint_heating
        elif self.zone.desired_room_temperature_setpoint_cooling:
            return self.zone.desired_room_temperature_setpoint_cooling
        else:
            return self.zone.desired_room_temperature_setpoint


class ZoneCurrentRoomTemperatureSensor(BaseZone, BaseTemperatureEntity):
    @property
    def name_suffix(self):
        return "Current Temperature"

    @property
    def id_suffix(self) -> str:
        return "current_temperature"

    @property
    def native_value(self):
        return (
            None
            if self.zone.current_room_temperature is None
            else round(self.zone.current_room_temperature, 1)
        )


class ZoneHumiditySensor(BaseZone, BaseHumidityEntity):
    @property
    def name_suffix(self):
        return "Humidity"

    @property
    def id_suffix(self) -> str:
        return "humidity"

    @property
    def native_value(self):
        return self.zone.current_room_humidity


class ZoneHeatingOperatingModeSensor(BaseZone, SensorEntity):
    @property
    def name_suffix(self):
        return "Heating Operating Mode"

    @property
    def id_suffix(self) -> str:
        return "heating_operating_mode"

    @property
    def native_value(self):
        return self.zone.heating.operation_mode_heating.display_value

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneHeatingStateSensor(BaseZone, SensorEntity):
    @property
    def name_suffix(self):
        return "Heating State"

    @property
    def id_suffix(self) -> str:
        return "heating_state"

    @property
    def native_value(self):
        return self.zone.heating_state.display_value

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneCurrentSpecialFunctionSensor(BaseZone, SensorEntity):
    @property
    def name_suffix(self):
        return "Current Special Function"

    @property
    def id_suffix(self) -> str:
        return "current_special_function"

    @property
    def native_value(self):
        return self.zone.current_special_function.display_value

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneQuickVetoDurationNumber(BaseZone, NumberEntity):
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:rocket-launch"

    @property
    def name_suffix(self):
        return "Quick Veto Duration"

    @property
    def id_suffix(self) -> str:
        return "quick_veto_duration"

    @property
    def native_value(self):
        return (
            round(self.zone.quick_veto_remaining.total_seconds() / 3600)
            if self.zone.quick_veto_remaining
            else 0
        )

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_quick_veto_zone_temperature(self.zone)
            await self.coordinator.async_request_refresh_delayed()
        else:
            await self.coordinator.api.quick_veto_zone_duration(self.zone, value)
            await self.coordinator.async_request_refresh_delayed()

    @property
    def available(self) -> bool:
        return self.zone.quick_veto_ongoing


class ZoneClimate(BaseZone, ClimateEntity):
    """Climate for a zone."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [str(k) for k in ZONE_HVAC_MODE_MAP.keys()]
    _attr_preset_modes = [str(k) for k in ZONE_PRESET_MAP.keys()]

    def __init__(
        self,
        system_index: int,
        zone_index: int,
        coordinator: SystemCoordinator,
        config: ConfigEntry,
    ) -> None:
        super().__init__(system_index, zone_index, coordinator)
        self.config = config

    @property
    def id_suffix(self) -> str:
        return "climate"

    @property
    def name_suffix(self):
        return "Climate"

    @property
    def default_quick_veto_duration(self):
        return self.config.options.get(
            OPTION_DEFAULT_QUICK_VETO_DURATION, DEFAULT_QUICK_VETO_DURATION
        )

    @property
    def time_program_overwrite(self):
        return self.config.options.get(
            OPTION_TIME_PROGRAM_OVERWRITE, DEFAULT_TIME_PROGRAM_OVERWRITE
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program_heating": self.zone.heating.time_program_heating,
            "quick_veto_start_date_time": self.zone.quick_veto_start_date_time,
            "quick_veto_end_date_time": self.zone.quick_veto_end_date_time,
            "holiday_start_date_time": self.zone.general.holiday_start_date_time,
            "holiday_end_date_time": self.zone.general.holiday_end_date_time,
        }
        return attr | self.zone.extra_fields

    async def set_holiday(self, **kwargs):
        _LOGGER.debug(
            "Setting holiday mode on System %s with params %s",
            self.system.id,
            kwargs,
        )
        start = kwargs.get("start")
        end = kwargs.get("end")
        duration_hours = kwargs.get("duration_hours")
        if duration_hours:
            if end:
                raise ValueError(
                    "Can't set end and duration_hours arguments at the same time for set_holiday"
                )
            if not start:
                start = datetime.now(self.system.timezone)
            end = start + timedelta(hours=duration_hours)
        await self.coordinator.api.set_holiday(self.system, start, end)
        await self.coordinator.async_request_refresh_delayed()

    async def cancel_holiday(self):
        _LOGGER.debug("Canceling holiday on System %s", self.system.id)
        await self.coordinator.api.cancel_holiday(self.system)
        await self.coordinator.async_request_refresh_delayed()

    async def set_zone_time_program(self, **kwargs):
        _LOGGER.debug("Canceling holiday on System %s", self.system.id)
        program_type = kwargs.get("program_type")
        time_program = ZoneTimeProgram.from_api(**kwargs.get("time_program"))
        await self.coordinator.api.set_zone_time_program(
            self.zone, program_type, time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_quick_veto(self, **kwargs):
        _LOGGER.debug("Setting quick veto on %s with params %s", self.zone.name, kwargs)
        temperature = kwargs.get("temperature")
        duration_hours = kwargs.get("duration_hours")
        await self.coordinator.api.quick_veto_zone_temperature(
            self.zone, temperature, duration_hours, self.default_quick_veto_duration
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_manual_mode_setpoint(self, **kwargs):
        _LOGGER.debug(
            f"Setting manual mode setpoint temperature on {self.zone.name} with params {kwargs}"
        )
        temperature = kwargs.get("temperature")
        setpoint_type = kwargs.get("setpoint_type", DEFAULT_MANUAL_SETPOINT_TYPE)
        await self.coordinator.api.set_manual_mode_setpoint(
            self.zone, temperature, setpoint_type
        )
        await self.coordinator.async_request_refresh_delayed()

    async def remove_quick_veto(self):
        _LOGGER.debug("Removing quick veto on %s", self.zone.name)
        await self.coordinator.api.cancel_quick_veto_zone_temperature(self.zone)
        await self.coordinator.async_request_refresh_delayed()

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def target_temperature(self) -> float | None:
        return self.zone.desired_room_temperature_setpoint

    @property
    def current_temperature(self) -> float | None:
        return self.zone.current_room_temperature

    @property
    def current_humidity(self) -> float | None:
        return self.zone.current_room_humidity

    @property
    def hvac_mode(self) -> HVACMode:
        return [
            k
            for k, v in ZONE_HVAC_MODE_MAP.items()
            if v == self.zone.heating.operation_mode_heating
        ][0]

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_zone_heating_operating_mode(
            self.zone,
            ZONE_HVAC_MODE_MAP[hvac_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """
        Set new target temperature. Depending on heating mode this sets the manual mode setpoint,
        or it creates a quick veto
        """
        _LOGGER.debug(
            "Setting temperature on %s with params %s", self.zone.name, kwargs
        )
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if not temperature:
            return

        if self.zone.heating.operation_mode_heating == ZoneHeatingOperatingMode.MANUAL:
            _LOGGER.debug(
                f"Setting manual mode setpoint on {self.zone.name} to {temperature}"
            )
            await self.set_manual_mode_setpoint(temperature=temperature)
            await self.coordinator.async_request_refresh_delayed()
        else:
            if self.time_program_overwrite and not self.preset_mode == PRESET_BOOST:
                _LOGGER.debug(
                    "Setting time program temperature in %s to %s",
                    self.zone.name,
                    temperature,
                )
                await self.coordinator.api.set_time_program_temperature(
                    self.zone,
                    "heating",  # TODO: Cooling?
                    temperature=temperature,
                )
            else:
                _LOGGER.debug(
                    "Setting quick veto on %s to %s", self.zone.name, temperature
                )
                await self.set_quick_veto(temperature=temperature)
            await self.coordinator.async_request_refresh_delayed()

    @property
    def preset_mode(self) -> PRESET_BOOST | PRESET_NONE:
        return [
            k
            for k, v in ZONE_PRESET_MAP.items()
            if v == self.zone.current_special_function
        ][0]

    async def async_set_preset_mode(self, preset_mode):
        """
        When setting a new preset, sometimes the old one needs to be canceled

        :param preset_mode:
        :return:
        """
        if preset_mode not in ZONE_PRESET_MAP:
            raise ValueError(
                f'Invalid preset mode, use one of {", ".join(ZONE_PRESET_MAP.keys())}'
            )
        requested_mode = ZONE_PRESET_MAP[preset_mode]
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
                    await self.cancel_holiday()
            if requested_mode == ZoneCurrentSpecialFunction.QUICK_VETO:
                await self.coordinator.api.quick_veto_zone_temperature(
                    self.zone,
                    self.zone.heating.manual_mode_setpoint_heating,
                    default_duration=self.default_quick_veto_duration,
                )
            if requested_mode == ZoneCurrentSpecialFunction.HOLIDAY:
                await self.set_holiday()

            if requested_mode == ZoneCurrentSpecialFunction.SYSTEM_OFF:
                # SYSTEM_OFF is a valid special function, but since there's no API endpoint we
                # just turn off the system though the zone heating mode API.
                # See https://github.com/signalkraft/mypyllant-component/issues/27#issuecomment-1746568372
                await self.async_set_hvac_mode(HVACMode.OFF)

            await self.coordinator.async_request_refresh_delayed()
