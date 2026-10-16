from __future__ import annotations

from typing import Mapping, Any

from homeassistant.components.climate import (
    HVACMode,
    FAN_OFF,
    FAN_ON,
    FAN_LOW,
    FAN_AUTO,
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers import selector

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.decorators import ensure_token_refresh
from custom_components.mypyllant.utils import VentilationEntity
from myPyllant.enums import (
    VentilationOperationMode,
    VentilationFanStageType,
    VentilationOperationModeVRC700,
)

VENTILATION_HVAC_MODE_MAP = {
    HVACMode.FAN_ONLY: VentilationOperationMode.NORMAL,
    HVACMode.AUTO: VentilationOperationMode.TIME_CONTROLLED,
}
_FAN_STAGE_TYPE_OPTIONS = [
    selector.SelectOptionDict(value=v.value, label=v.value.title())
    for v in VentilationFanStageType
]

# VRC700 ventilation only accepts DAY / SET_BACK / AUTO on the operation-mode
# endpoint; OFF / NORMAL / REDUCED are rejected with HTTP 400
# (MalformedRequestParameters / G003). The read-side ``fan_mode_map`` keeps the
# full set so the displayed ``fan_mode`` stays correct whatever the device
# reports, while writes must use this VRC700-specific mapping.
# Verified against the myVAILLANT API on a recoVAIR VAR 260/4 (VRC700).
VRC700_FAN_MODE_WRITE_MAP = {
    FAN_ON: VentilationOperationModeVRC700.DAY,
    FAN_LOW: VentilationOperationModeVRC700.SET_BACK,
    FAN_AUTO: VentilationOperationModeVRC700.AUTO,
}


class VentilationClimate(VentilationEntity, ClimateEntity):
    """
    Used in climate platform
    """

    _attr_hvac_modes = list(VENTILATION_HVAC_MODE_MAP.keys())
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_climate"

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Climate"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program_ventilation": self.ventilation.time_program_ventilation,
            "maximum_day_fan_stage": self.ventilation.maximum_day_fan_stage,
            "maximum_night_fan_stage": self.ventilation.maximum_night_fan_stage,
        }
        return attr

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.FAN_MODE

    @property
    def fan_mode_map(self):
        if self.ventilation.control_identifier.is_vrc700:
            return {
                VentilationOperationModeVRC700.OFF: FAN_OFF,
                VentilationOperationModeVRC700.NORMAL: FAN_ON,
                VentilationOperationModeVRC700.REDUCED: FAN_LOW,
                VentilationOperationModeVRC700.AUTO: FAN_AUTO,
                VentilationOperationModeVRC700.DAY: FAN_ON,
                VentilationOperationModeVRC700.SET_BACK: FAN_LOW,
            }
        else:
            return {
                VentilationOperationMode.OFF: FAN_OFF,
                VentilationOperationMode.NORMAL: FAN_ON,
                VentilationOperationMode.REDUCED: FAN_LOW,
                VentilationOperationMode.TIME_CONTROLLED: FAN_AUTO,
            }

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

    @property
    def fan_modes(self) -> list[str]:
        if self.ventilation.control_identifier.is_vrc700:
            return list(VRC700_FAN_MODE_WRITE_MAP.keys())
        return [str(k) for k in self.fan_mode_map.values()]

    @ensure_token_refresh
    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            VENTILATION_HVAC_MODE_MAP[hvac_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def fan_mode(self) -> HVACMode:
        return self.fan_mode_map[self.ventilation.operation_mode_ventilation]

    @ensure_token_refresh
    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if self.ventilation.control_identifier.is_vrc700:
            mode = VRC700_FAN_MODE_WRITE_MAP[fan_mode]
        else:
            mode = [k for k, v in self.fan_mode_map.items() if v == fan_mode][0]
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            mode,
        )
        await self.coordinator.async_request_refresh_delayed()

    @ensure_token_refresh
    async def set_ventilation_fan_stage(
        self, maximum_fan_stage: int | str, **kwargs: Any
    ) -> None:
        await self.coordinator.api.set_ventilation_fan_stage(
            self.ventilation,
            int(maximum_fan_stage),
            VentilationFanStageType(kwargs.get("fan_stage_type")),
        )
        await self.coordinator.async_request_refresh_delayed()
