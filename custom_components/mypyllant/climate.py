from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

import voluptuous as vol
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
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform, selector
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import as_datetime
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from myPyllant.const import (
    DEFAULT_MANUAL_SETPOINT_TYPE,
    DEFAULT_QUICK_VETO_DURATION,
    MANUAL_SETPOINT_TYPES,
)
from myPyllant.models import (
    System,
    Zone,
    ZoneCurrentSpecialFunction,
    ZoneHeatingOperatingMode,
    ZoneTimeProgram,
)

from . import SystemCoordinator
from .const import (
    DOMAIN,
    OPTION_DEFAULT_QUICK_VETO_DURATION,
    SERVICE_CANCEL_HOLIDAY,
    SERVICE_CANCEL_QUICK_VETO,
    SERVICE_SET_HOLIDAY,
    SERVICE_SET_MANUAL_MODE_SETPOINT,
    SERVICE_SET_QUICK_VETO,
    SERVICE_SET_ZONE_TIME_PROGRAM,
)

_LOGGER = logging.getLogger(__name__)

_MANUAL_SETPOINT_TYPES_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in MANUAL_SETPOINT_TYPES.items()
]

HVAC_MODE_MAP = {
    HVACMode.OFF: ZoneHeatingOperatingMode.OFF,
    HVACMode.HEAT_COOL: ZoneHeatingOperatingMode.MANUAL,
    HVACMode.AUTO: ZoneHeatingOperatingMode.TIME_CONTROLLED,
}

PRESET_MAP = {
    PRESET_BOOST: ZoneCurrentSpecialFunction.QUICK_VETO,
    PRESET_NONE: ZoneCurrentSpecialFunction.NONE,
    PRESET_AWAY: ZoneCurrentSpecialFunction.HOLIDAY,
    PRESET_SLEEP: ZoneCurrentSpecialFunction.SYSTEM_OFF,
}


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    default_quick_veto_duration = config.options.get(
        OPTION_DEFAULT_QUICK_VETO_DURATION, DEFAULT_QUICK_VETO_DURATION
    )
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping climate")
        return

    climates: list[ClimateEntity] = []

    for index, system in enumerate(coordinator.data):
        for zone_index, zone in enumerate(system.zones):
            climates.append(
                ZoneClimate(index, zone_index, coordinator, default_quick_veto_duration)
            )

    async_add_entities(climates)

    if len(climates) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up climate entity services for %s", platform)
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_QUICK_VETO,
            {
                vol.Required("temperature"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=0, max=30)
                ),
                vol.Optional("duration_hours"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=1)
                ),
            },
            "set_quick_veto",
        )
        platform.async_register_entity_service(
            SERVICE_SET_MANUAL_MODE_SETPOINT,
            {
                vol.Required("temperature"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=0, max=30)
                ),
                vol.Required("setpoint_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_MANUAL_SETPOINT_TYPES_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
            },
            "set_manual_mode_setpoint",
        )
        platform.async_register_entity_service(
            SERVICE_CANCEL_QUICK_VETO,
            {},
            "remove_quick_veto",
        )
        # noinspection PyTypeChecker
        platform.async_register_entity_service(
            SERVICE_SET_HOLIDAY,
            {
                vol.Optional("start"): vol.Coerce(as_datetime),
                vol.Optional("end"): vol.Coerce(as_datetime),
                vol.Optional("duration_hours"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=1)
                ),
            },
            "set_holiday",
        )
        platform.async_register_entity_service(
            SERVICE_CANCEL_HOLIDAY,
            {},
            "cancel_holiday",
        )
        platform.async_register_entity_service(
            SERVICE_SET_ZONE_TIME_PROGRAM,
            {
                vol.Required("program_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value="heating", label="Heating"),
                            selector.SelectOptionDict(value="cooling", label="Cooling"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("time_program"): vol.All(dict),
            },
            "set_zone_time_program",
        )


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
        default_quick_veto_duration: int,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index
        self.entity_id = f"{DOMAIN}.zone_{zone_index}"
        self.default_quick_veto_duration = default_quick_veto_duration

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
            name=self.name,
            manufacturer=self.system.brand_name,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_climate_zone_{self.zone_index}"

    @property
    def name(self) -> str:
        return self.zone.name

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_windows": self.zone.heating.time_program_heating,
            "quick_veto_start_date_time": self.zone.quick_veto_start_date_time,
            "quick_veto_end_date_time": self.zone.quick_veto_end_date_time,
        }
        return attr

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
                start = datetime.now()
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
            for k, v in HVAC_MODE_MAP.items()
            if v == self.zone.heating.operation_mode_heating
        ][0]

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_zone_heating_operating_mode(
            self.zone,
            HVAC_MODE_MAP[hvac_mode],
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
            _LOGGER.debug("Setting quick veto on %s to %s", self.zone.name, temperature)
            await self.set_quick_veto(temperature=temperature)
            await self.coordinator.async_request_refresh_delayed()

    @property
    def preset_mode(self) -> PRESET_BOOST | PRESET_NONE:
        return [
            k for k, v in PRESET_MAP.items() if v == self.zone.current_special_function
        ][0]

    async def async_set_preset_mode(self, preset_mode):
        """
        When setting a new preset, sometimes the old one needs to be canceled

        :param preset_mode:
        :return:
        """
        if preset_mode not in PRESET_MAP:
            raise ValueError(
                f'Invalid preset mode, use one of {", ".join(PRESET_MAP.keys())}'
            )
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
                    self.zone.heating.manual_mode_setpoint_heating,
                    default_duration=self.default_quick_veto_duration,
                )
            if requested_mode == ZoneCurrentSpecialFunction.HOLIDAY:
                await self.coordinator.api.set_holiday(self.system)

            if requested_mode == ZoneCurrentSpecialFunction.SYSTEM_OFF:
                # SYSTEM_OFF is a valid special function, but since there's no API endpoint we
                # just turn off the system though the zone heating mode API.
                # See https://github.com/signalkraft/mypyllant-component/issues/27#issuecomment-1746568372
                await self.async_set_hvac_mode(HVACMode.OFF)

            await self.coordinator.async_request_refresh_delayed()
