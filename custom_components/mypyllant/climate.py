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
    FAN_AUTO,
    FAN_LOW,
    FAN_OFF,
    FAN_ON,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_NONE,
    PRESET_SLEEP,
    PRESET_ECO,
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
    Ventilation,
    Zone,
    ZoneTimeProgram,
)
from myPyllant.enums import (
    ZoneHeatingOperatingMode,
    ZoneHeatingOperatingModeVRC700,
    ZoneCurrentSpecialFunction,
    VentilationOperationMode,
    VentilationFanStageType,
)

from custom_components.mypyllant.utils import shorten_zone_name

from . import SystemCoordinator
from .const import (
    DEFAULT_TIME_PROGRAM_OVERWRITE,
    DOMAIN,
    OPTION_DEFAULT_QUICK_VETO_DURATION,
    OPTION_TIME_PROGRAM_OVERWRITE,
    SERVICE_CANCEL_HOLIDAY,
    SERVICE_CANCEL_QUICK_VETO,
    SERVICE_SET_HOLIDAY,
    SERVICE_SET_MANUAL_MODE_SETPOINT,
    SERVICE_SET_QUICK_VETO,
    SERVICE_SET_VENTILATION_FAN_STAGE,
    SERVICE_SET_ZONE_TIME_PROGRAM,
    OPTION_DEFAULT_HOLIDAY_SETPOINT,
    DEFAULT_HOLIDAY_SETPOINT,
)

_LOGGER = logging.getLogger(__name__)

_MANUAL_SETPOINT_TYPES_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in MANUAL_SETPOINT_TYPES.items()
]

ZONE_PRESET_MAP = {
    PRESET_BOOST: ZoneCurrentSpecialFunction.QUICK_VETO,
    PRESET_ECO: ZoneCurrentSpecialFunction.NONE,
    PRESET_NONE: ZoneCurrentSpecialFunction.NONE,
    PRESET_AWAY: ZoneCurrentSpecialFunction.HOLIDAY,
    PRESET_SLEEP: ZoneCurrentSpecialFunction.SYSTEM_OFF,
}

VENTILATION_HVAC_MODE_MAP = {
    HVACMode.FAN_ONLY: VentilationOperationMode.NORMAL,
    HVACMode.AUTO: VentilationOperationMode.TIME_CONTROLLED,
}

VENTILATION_FAN_MODE_MAP = {
    FAN_OFF: VentilationOperationMode.OFF,
    FAN_ON: VentilationOperationMode.NORMAL,
    FAN_LOW: VentilationOperationMode.REDUCED,
    FAN_AUTO: VentilationOperationMode.TIME_CONTROLLED,
}

_FAN_STAGE_TYPE_OPTIONS = [
    selector.SelectOptionDict(value=v.value, label=v.value.title())
    for v in VentilationFanStageType
]


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping climate")
        return

    zone_entities: list[ClimateEntity] = []
    ventilation_entities: list[ClimateEntity] = []

    for index, system in enumerate(coordinator.data):
        for zone_index, _ in enumerate(system.zones):
            zone_entities.append(
                ZoneClimate(
                    index,
                    zone_index,
                    coordinator,
                    config,
                )
            )
        for ventilation_index, _ in enumerate(system.ventilation):
            ventilation_entities.append(
                VentilationClimate(
                    index,
                    ventilation_index,
                    coordinator,
                )
            )

    async_add_entities(zone_entities)
    async_add_entities(ventilation_entities)

    if len(zone_entities) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up zone climate entity services for %s", platform)
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
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
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
                vol.Optional("setpoint"): vol.All(vol.Coerce(float), vol.Clamp(min=0)),
            },
            "set_holiday",
        )
        platform.async_register_entity_service(
            SERVICE_CANCEL_HOLIDAY,
            {},
            "cancel_holiday",
        )
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
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

    if len(ventilation_entities) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up ventilation climate entity services for %s", platform)
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_VENTILATION_FAN_STAGE,
            {
                vol.Required("maximum_fan_stage"): vol.All(
                    vol.Coerce(int), vol.Clamp(min=1, max=6)
                ),
                vol.Required("fan_stage_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_FAN_STAGE_TYPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    ),
                ),
            },
            "set_ventilation_fan_stage",
        )


class ZoneClimate(CoordinatorEntity, ClimateEntity):
    """Climate for a zone."""

    coordinator: SystemCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_preset_modes = [str(k) for k in ZONE_PRESET_MAP.keys()]

    def __init__(
        self,
        system_index: int,
        zone_index: int,
        coordinator: SystemCoordinator,
        config: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index
        self.config = config

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [k for k in self.hvac_mode_map.keys()]

    @property
    def hvac_mode_map(self):
        if self.zone.control_identifier.is_vrc700:
            return {
                HVACMode.OFF: ZoneHeatingOperatingModeVRC700.OFF,
                HVACMode.HEAT_COOL: ZoneHeatingOperatingModeVRC700.DAY,
                HVACMode.AUTO: ZoneHeatingOperatingModeVRC700.AUTO,
            }
        else:
            return {
                HVACMode.OFF: ZoneHeatingOperatingMode.OFF,
                HVACMode.HEAT_COOL: ZoneHeatingOperatingMode.MANUAL,
                HVACMode.AUTO: ZoneHeatingOperatingMode.TIME_CONTROLLED,
            }

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
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_climate"

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Climate"

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
        setpoint = kwargs.get("setpoint")
        if duration_hours:
            if end:
                raise ValueError(
                    "Can't set end and duration_hours arguments at the same time for set_holiday"
                )
            if not start:
                start = datetime.now(self.system.timezone)
            end = start + timedelta(hours=duration_hours)
        if self.system.control_identifier.is_vrc700 and setpoint is None:
            setpoint = self.config.options.get(
                OPTION_DEFAULT_HOLIDAY_SETPOINT, DEFAULT_HOLIDAY_SETPOINT
            )
        await self.coordinator.api.set_holiday(
            self.system, start, end, setpoint=setpoint
        )
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
        if self.zone.is_eco_mode:
            return self.zone.heating.set_back_temperature
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
            for k, v in self.hvac_mode_map.items()
            if v == self.zone.heating.operation_mode_heating
        ][0]

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_zone_heating_operating_mode(
            self.zone,
            self.hvac_mode_map[hvac_mode],
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
    def preset_mode(self) -> str:
        if self.zone.is_eco_mode:
            return PRESET_ECO
        return [
            k
            for k, v in ZONE_PRESET_MAP.items()
            if v == self.zone.current_special_function
        ][0]

    async def async_set_preset_mode(self, preset_mode):
        """
        When setting a new preset, sometimes the old one needs to be canceled

        Parameters:
            preset_mode (str): The new preset mode to set
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


class VentilationClimate(CoordinatorEntity, ClimateEntity):
    coordinator: SystemCoordinator
    _attr_fan_modes = [str(k) for k in VENTILATION_FAN_MODE_MAP.keys()]
    _attr_hvac_modes = [str(k) for k in VENTILATION_HVAC_MODE_MAP.keys()]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        system_index: int,
        ventilation_index: int,
        coordinator: SystemCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.ventilation_index = ventilation_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def ventilation(self) -> Ventilation:
        return self.system.ventilation[self.ventilation_index]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_climate"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_ventilation_{self.ventilation_index}"

    @property
    def name_prefix(self) -> str:
        vname = [d for d in self.system.devices if d.type == "ventilation"][
            0
        ].name_display
        return f"{self.system.home.home_name or self.system.home.nomenclature} Ventilation {vname}"

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Climate"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program_ventilation": self.ventilation.time_program_ventilation,
        }
        return attr

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.FAN_MODE

    @property
    def hvac_mode(self) -> HVACMode:
        if (
            self.ventilation.operation_mode_ventilation
            in VENTILATION_HVAC_MODE_MAP.values()
        ):
            return [
                k
                for k, v in VENTILATION_HVAC_MODE_MAP.items()
                if v == self.ventilation.operation_mode_ventilation
            ][0]
        else:
            return HVACMode.FAN_ONLY

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            VENTILATION_HVAC_MODE_MAP[hvac_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def fan_mode(self) -> HVACMode:
        return [
            k
            for k, v in VENTILATION_FAN_MODE_MAP.items()
            if v == self.ventilation.operation_mode_ventilation
        ][0]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            VENTILATION_FAN_MODE_MAP[fan_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_ventilation_fan_stage(
        self, maximum_fan_stage: int | str, **kwargs: Any
    ) -> None:
        await self.coordinator.api.set_ventilation_fan_stage(
            self.ventilation,
            int(maximum_fan_stage),
            VentilationFanStageType(kwargs.get("fan_stage_type")),
        )
        await self.coordinator.async_request_refresh_delayed()
