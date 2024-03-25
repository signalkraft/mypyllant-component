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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.coordinator import SystemCoordinator
from myPyllant.enums import (
    VentilationOperationMode,
    VentilationFanStageType,
    VentilationOperationModeVRC700,
)
from myPyllant.models import System, Ventilation

VENTILATION_HVAC_MODE_MAP = {
    HVACMode.FAN_ONLY: VentilationOperationMode.NORMAL,
    HVACMode.AUTO: VentilationOperationMode.TIME_CONTROLLED,
}
_FAN_STAGE_TYPE_OPTIONS = [
    selector.SelectOptionDict(value=v.value, label=v.value.title())
    for v in VentilationFanStageType
]


class VentilationClimate(CoordinatorEntity, ClimateEntity):
    """
    Used in climate platform
    """

    coordinator: SystemCoordinator
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
        return [str(k) for k in self.fan_mode_map.values()]

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            VENTILATION_HVAC_MODE_MAP[hvac_mode],
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def fan_mode(self) -> HVACMode:
        return self.fan_mode_map[self.ventilation.operation_mode_ventilation]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        mode = [k for k, v in self.fan_mode_map.items() if v == fan_mode][0]
        await self.coordinator.api.set_ventilation_operation_mode(
            self.ventilation,
            mode,
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
