from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
)
from homeassistant.const import UnitOfTemperature
from myPyllant.models import (
    System,
    Ventilation,
    VentilationFanStageType,
    VentilationOperationMode,
    ZoneCurrentSpecialFunction,
    ZoneHeatingOperatingMode,
)
from custom_components.mypyllant import SystemCoordinator

from custom_components.mypyllant.entities.base import BaseSystemCoordinator


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


class VentilationClimate(BaseSystemCoordinator, ClimateEntity):
    _attr_fan_modes = [str(k) for k in VENTILATION_FAN_MODE_MAP.keys()]
    _attr_hvac_modes = [str(k) for k in VENTILATION_HVAC_MODE_MAP.keys()]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        system_index: int,
        ventilation_index: int,
        coordinator: SystemCoordinator,
    ) -> None:
        super().__init__(system_index, coordinator)
        self.ventilation_index = ventilation_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def ventilation(self) -> Ventilation:
        return self.system.ventilation[self.ventilation_index]

    @property
    def id_suffix(self) -> str:
        return "climate"

    @property
    def name_suffix(self) -> str:
        return "Climate"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_ventilation_{self.ventilation_index}"

    @property
    def name_prefix(self) -> str:
        vname = [d for d in self.system.devices if d.type == "ventilation"][
            0
        ].name_display
        return f"{super().name_prefix} Ventilation {vname}"

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
        return [
            k
            for k, v in VENTILATION_HVAC_MODE_MAP.items()
            if v == self.ventilation.operation_mode_ventilation
        ][0]

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
