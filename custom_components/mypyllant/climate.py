from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
    PRESET_COMFORT,
)
from homeassistant.components.climate.const import (
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
    ZONE_MANUAL_SETPOINT_TYPES,
)
from myPyllant.models import (
    System,
    Zone,
    ZoneTimeProgram,
    AmbisenseRoom,
    RoomTimeProgram,
)
from myPyllant.enums import (
    ZoneHeatingOperatingMode,
    ZoneHeatingOperatingModeVRC700,
    ZoneCurrentSpecialFunction,
    CircuitState,
    AmbisenseRoomOperationMode,
)

from custom_components.mypyllant.utils import shorten_zone_name, EntityList

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
    SERVICE_SET_ZONE_OPERATING_MODE,
    SERVICE_SET_TIME_PROGRAM,
)
from .ventilation_climate import _FAN_STAGE_TYPE_OPTIONS, VentilationClimate

_LOGGER = logging.getLogger(__name__)

_ZONE_MANUAL_SETPOINT_TYPES_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in ZONE_MANUAL_SETPOINT_TYPES.items()
]

_ZONE_OPERATING_MODE_OPTIONS = [
    selector.SelectOptionDict(value=v, label=v.replace("_", " ").title())
    for v in set(
        [
            e.value
            for e in list(ZoneHeatingOperatingMode)
            + list(ZoneHeatingOperatingModeVRC700)
        ]
    )
]

ZONE_PRESET_MAP = {
    PRESET_BOOST: ZoneCurrentSpecialFunction.QUICK_VETO,
    PRESET_ECO: ZoneCurrentSpecialFunction.NONE,
    PRESET_NONE: ZoneCurrentSpecialFunction.NONE,
    PRESET_AWAY: ZoneCurrentSpecialFunction.HOLIDAY,
    PRESET_SLEEP: ZoneCurrentSpecialFunction.SYSTEM_OFF,
}

ZONE_PRESET_MAP_VRC700 = {
    ZoneHeatingOperatingModeVRC700.OFF: PRESET_NONE,
    ZoneHeatingOperatingModeVRC700.DAY: PRESET_COMFORT,
    ZoneHeatingOperatingModeVRC700.AUTO: PRESET_NONE,
    ZoneHeatingOperatingModeVRC700.SET_BACK: PRESET_ECO,
}

ZONE_HVAC_ACTION_MAP = {
    CircuitState.STANDBY: HVACAction.IDLE,
    CircuitState.HEATING: HVACAction.HEATING,
    CircuitState.COOLING: HVACAction.COOLING,
}

AMBISENSE_ROOM_OPERATION_MODE_MAP = {
    AmbisenseRoomOperationMode.OFF: HVACMode.OFF,
    AmbisenseRoomOperationMode.AUTO: HVACMode.AUTO,
    AmbisenseRoomOperationMode.MANUAL: HVACMode.HEAT_COOL,
}

AMBISENSE_ROOM_PRESETS = [PRESET_NONE, PRESET_BOOST]


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

    zone_entities: EntityList[ClimateEntity] = EntityList()
    ventilation_entities: EntityList[ClimateEntity] = EntityList()
    ambisense_entities: EntityList[ClimateEntity] = EntityList()

    for index, system in enumerate(coordinator.data):
        for zone_index, _ in enumerate(system.zones):
            data_key = f"zone_{index}_{zone_index}"
            if data_key not in hass.data[DOMAIN][config.entry_id]:
                hass.data[DOMAIN][config.entry_id][data_key] = {}
            zone_entities.append(
                lambda: ZoneClimate(
                    index,
                    zone_index,
                    coordinator,
                    config,
                    hass.data[DOMAIN][config.entry_id][data_key],
                )
            )

        for room in system.ambisense_rooms:
            ambisense_entities.append(
                lambda: AmbisenseClimate(
                    index,
                    room.room_index,
                    coordinator,
                    config,
                    hass.data[DOMAIN][config.entry_id][data_key],
                )
            )

        for ventilation_index, _ in enumerate(system.ventilation):
            ventilation_entities.append(
                lambda: VentilationClimate(
                    index,
                    ventilation_index,
                    coordinator,
                )
            )

    async_add_entities(zone_entities)
    async_add_entities(ventilation_entities)
    async_add_entities(ambisense_entities)

    if len(zone_entities) > 0 or len(ambisense_entities) > 0:
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
                vol.Optional("setpoint_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_ZONE_MANUAL_SETPOINT_TYPES_OPTIONS,
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
        # Wrapping the schema in vol.Schema() breaks entity_id passing
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
            SERVICE_SET_TIME_PROGRAM,
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
            "set_time_program",
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

        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_ZONE_OPERATING_MODE,
            {
                vol.Required("mode"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_ZONE_OPERATING_MODE_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required("operating_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value="heating", label="Heating"),
                            selector.SelectOptionDict(value="cooling", label="Cooling"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            },
            "set_zone_operating_mode",
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
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        system_index: int,
        zone_index: int,
        coordinator: SystemCoordinator,
        config: ConfigEntry,
        data: dict,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index
        self.config = config
        self.data = data
        self.data["last_active_hvac_mode"] = (
            self.hvac_mode if self.hvac_mode != HVACMode.OFF else HVACMode.AUTO
        )
        _LOGGER.debug(
            "Saving last active HVAC mode %s", self.data["last_active_hvac_mode"]
        )

    async def async_update(self) -> None:
        """
        Save last active HVAC mode after update, so it can be restored in turn_on
        """
        await super().async_update()

        if self.enabled and self.hvac_mode != HVACMode.OFF:
            _LOGGER.debug("Saving last active HVAC mode %s", self.hvac_mode)
            self.data["last_active_hvac_mode"] = self.hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return list(set([v for v in self.hvac_mode_map.values()]))

    @property
    def hvac_mode_map(self):
        if self.zone.control_identifier.is_vrc700:
            return {
                ZoneHeatingOperatingModeVRC700.OFF: HVACMode.OFF,
                ZoneHeatingOperatingModeVRC700.AUTO: HVACMode.AUTO,
                ZoneHeatingOperatingModeVRC700.DAY: HVACMode.AUTO,
                ZoneHeatingOperatingModeVRC700.SET_BACK: HVACMode.AUTO,
            }
        else:
            return {
                ZoneHeatingOperatingMode.OFF: HVACMode.OFF,
                ZoneHeatingOperatingMode.MANUAL: HVACMode.HEAT_COOL,
                ZoneHeatingOperatingMode.TIME_CONTROLLED: HVACMode.AUTO,
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
        await self.coordinator.async_request_refresh_delayed(20)

    async def cancel_holiday(self):
        _LOGGER.debug("Canceling holiday on System %s", self.system.id)
        await self.coordinator.api.cancel_holiday(self.system)
        await self.coordinator.async_request_refresh_delayed(20)

    async def set_time_program(self, **kwargs):
        _LOGGER.debug("Setting time program on %s", self.zone)
        program_type = kwargs.get("program_type")
        time_program = ZoneTimeProgram.from_api(**kwargs.get("time_program"))
        await self.coordinator.api.set_zone_time_program(
            self.zone, program_type, time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_zone_time_program(self, **kwargs):
        _LOGGER.warning(
            "set_zone_time_program is deprecated and will be removed in the future. "
            "Use set_time_program instead"
        )
        await self.set_time_program(**kwargs)

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
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
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
        return self.hvac_mode_map.get(self.zone.heating.operation_mode_heating)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        mode = [k for k, v in self.hvac_mode_map.items() if v == hvac_mode][0]
        await self.set_zone_operating_mode(mode)

    async def set_zone_operating_mode(
        self,
        mode: ZoneHeatingOperatingMode | ZoneHeatingOperatingModeVRC700 | str,
        operating_type: str = "heating",
    ):
        """
        Set operating mode for either cooling and heating HVAC mode
        Used for service set_zone_operating_mode

        Parameters:
            mode: The new operating mode to set
            operating_type: Whether to set the mode for cooling or heating
        """
        if self.zone.control_identifier.is_vrc700:
            if mode not in ZoneHeatingOperatingModeVRC700:
                raise ValueError(
                    f"Invalid mode, use one of {', '.join(ZoneHeatingOperatingModeVRC700)}"
                )
        else:
            if mode not in ZoneHeatingOperatingMode:
                raise ValueError(
                    f"Invalid mode, use one of {', '.join(ZoneHeatingOperatingMode)}"
                )
        await self.coordinator.api.set_zone_operating_mode(
            self.zone,
            mode,
            operating_type,
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def hvac_action(self) -> HVACAction | None:
        circuit_state = self.zone.get_associated_circuit(self.system).circuit_state
        return ZONE_HVAC_ACTION_MAP.get(circuit_state)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(self.data["last_active_hvac_mode"])

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

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
                await self.coordinator.async_request_refresh_delayed()
            else:
                _LOGGER.debug(
                    "Setting quick veto on %s to %s", self.zone.name, temperature
                )
                await self.set_quick_veto(temperature=temperature)

    @property
    def preset_modes(self) -> list[str]:
        if self.zone.control_identifier.is_vrc700:
            return list({v for v in ZONE_PRESET_MAP_VRC700.values()})
        else:
            return [k for k in ZONE_PRESET_MAP.keys()]

    @property
    def preset_mode(self) -> str:
        if self.zone.control_identifier.is_vrc700:
            return ZONE_PRESET_MAP_VRC700[self.zone.heating.operation_mode_heating]  # type: ignore
        else:
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
        if self.zone.control_identifier.is_vrc700:
            # VRC700 presets map to operating modes instead of special functions
            if preset_mode == PRESET_NONE:
                # None can map to off or auto mode, if it's selected by the user we want auto
                requested_mode = ZoneHeatingOperatingModeVRC700.AUTO
            elif preset_mode in ZONE_PRESET_MAP_VRC700.values():
                requested_mode = [
                    k for k, v in ZONE_PRESET_MAP_VRC700.items() if v == preset_mode
                ][0]
            else:
                raise ValueError(
                    f'Invalid preset mode, use one of {", ".join(set(ZONE_PRESET_MAP_VRC700.values()))}'
                )
            await self.set_zone_operating_mode(requested_mode)
        else:
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


class AmbisenseClimate(CoordinatorEntity, ClimateEntity):
    """Climate for an ambisense room."""

    coordinator: SystemCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = list(
        set([v for v in AMBISENSE_ROOM_OPERATION_MODE_MAP.values()])
    )
    _attr_preset_modes = AMBISENSE_ROOM_PRESETS
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        system_index: int,
        room_index: int,
        coordinator: SystemCoordinator,
        config: ConfigEntry,
        data: dict,
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.room_index = room_index
        self.config = config
        self.data = data
        self.data["last_active_hvac_mode"] = (
            self.hvac_mode if self.hvac_mode != HVACMode.OFF else HVACMode.AUTO
        )
        _LOGGER.debug(
            "Saving last active HVAC mode %s", self.data["last_active_hvac_mode"]
        )

    async def async_update(self) -> None:
        """
        Save last active HVAC mode after update, so it can be restored in turn_on
        """
        await super().async_update()

        if self.enabled and self.hvac_mode != HVACMode.OFF:
            _LOGGER.debug("Saving last active HVAC mode %s", self.hvac_mode)
            self.data["last_active_hvac_mode"] = self.hvac_mode

    @property
    def default_quick_veto_duration(self):
        """
        Returns the default quick veto duration in minutes
        """
        return (
            self.config.options.get(
                OPTION_DEFAULT_QUICK_VETO_DURATION, DEFAULT_QUICK_VETO_DURATION
            )
            * 60  # Ambisense rooms expect minutes, but OPTION_DEFAULT_QUICK_VETO_DURATION is in hours
        )

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def room(self) -> AmbisenseRoom:
        return [
            r for r in self.system.ambisense_rooms if r.room_index == self.room_index
        ][0]

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_room_{self.room_index}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name,
            manufacturer=self.system.brand_name,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_climate"

    @property
    def name(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} {self.room.name}"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program": self.room.time_program,
            "quick_veto_end_date_time": self.room.room_configuration.quick_veto_end_time,
            "window_state": self.room.room_configuration.window_state,
            "button_lock": self.room.room_configuration.button_lock,
            "devices": [asdict(d) for d in self.room.room_configuration.devices],
        }
        return attr | self.room.extra_fields

    async def set_quick_veto(self, **kwargs):
        _LOGGER.debug("Setting quick veto on %s with params %s", self.room.name, kwargs)
        temperature = kwargs.get("temperature")
        if "duration_minutes" in kwargs:
            duration_minutes = kwargs.get("duration_minutes")
        elif "duration_hours" in kwargs:
            duration_minutes = kwargs.get("duration_hours") * 60
        else:
            duration_minutes = None
        await self.coordinator.api.quick_veto_ambisense_room(
            self.room, temperature, duration_minutes, self.default_quick_veto_duration
        )
        await self.coordinator.async_request_refresh_delayed()

    async def remove_quick_veto(self):
        _LOGGER.debug("Removing quick veto on %s", self.room.name)
        await self.coordinator.api.cancel_quick_veto_ambisense_room(self.room)
        await self.coordinator.async_request_refresh_delayed()

    async def set_manual_mode_setpoint(self, **kwargs):
        _LOGGER.debug(
            f"Setting manual mode setpoint temperature on {self.room.name} with params {kwargs}"
        )
        temperature = kwargs.get("temperature")
        await self.coordinator.api.set_ambisense_room_manual_mode_setpoint_temperature(
            self.room, temperature
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    @property
    def target_temperature(self) -> float | None:
        return self.room.room_configuration.temperature_setpoint

    @property
    def current_temperature(self) -> float | None:
        return self.room.room_configuration.current_temperature

    @property
    def current_humidity(self) -> float | None:
        return self.room.room_configuration.current_humidity

    @property
    def hvac_mode(self) -> HVACMode | None:
        if self.room.room_configuration.operation_mode:
            return AMBISENSE_ROOM_OPERATION_MODE_MAP.get(
                self.room.room_configuration.operation_mode, HVACMode.OFF
            )
        else:
            return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        mode = [
            k for k, v in AMBISENSE_ROOM_OPERATION_MODE_MAP.items() if v == hvac_mode
        ][0]
        await self.coordinator.api.set_ambisense_room_operation_mode(self.room, mode)
        await self.coordinator.async_request_refresh_delayed()

    @property
    def preset_mode(self) -> str | None:
        if self.room.room_configuration.quick_veto_end_time is not None:
            return PRESET_BOOST
        else:
            return PRESET_NONE

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_NONE:
            await self.remove_quick_veto()
        # Both preset none and boost exist, but going from none to boost makes no sense without a specific
        # target temperature
        self._valid_mode_or_raise("preset", preset_mode, [PRESET_NONE])

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(self.data["last_active_hvac_mode"])

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """
        Set new target temperature. Depending on heating mode this sets the manual mode setpoint,
        or it creates a quick veto
        """
        _LOGGER.debug(
            "Setting temperature on %s with params %s", self.room.name, kwargs
        )
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if not temperature:
            return

        if (
            self.room.room_configuration.operation_mode
            == AmbisenseRoomOperationMode.MANUAL
        ):
            await self.set_manual_mode_setpoint(temperature=temperature)
        else:
            await self.set_quick_veto(temperature=temperature)

    async def set_time_program(self, **kwargs):
        _LOGGER.debug("Setting time program on %s", self.room)
        if "program_type" in kwargs:
            _LOGGER.warning(
                "program_type is not supported in Ambisense room time programs"
            )
        time_program = RoomTimeProgram.from_api(**kwargs.get("time_program"))
        await self.coordinator.api.set_ambisense_room_time_program(
            self.room, time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_zone_time_program(self, **kwargs):
        _LOGGER.warning(
            "set_zone_time_program is deprecated and will be removed in the future. "
            "Use set_time_program instead"
        )
        await self.set_time_program(**kwargs)

    async def set_holiday(self, **kwargs):
        raise NotImplementedError("Ambisense rooms do not support holiday mode")

    async def cancel_holiday(self):
        raise NotImplementedError("Ambisense rooms do not support holiday mode")

    async def set_zone_operating_mode(self):
        raise NotImplementedError("Ambisense rooms do not support zone operating mode")
