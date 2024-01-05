from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.entities.base import (
    BaseSystemCoordinator,
    BaseTemperatureEntity,
)
from myPyllant.models import (
    DHWCurrentSpecialFunction,
    DHWOperationMode,
    DHWTimeProgram,
    DomesticHotWater,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorEntity

from collections.abc import Mapping
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from myPyllant.utils import prepare_field_value_for_dict
from homeassistant.components.switch import SwitchEntity


class BaseDomesticHotWater(BaseSystemCoordinator):
    def __init__(
        self, system_index: int, dhw_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(system_index, coordinator)
        self.system_index = system_index
        self.dhw_index = dhw_index

    @property
    def name_prefix(self) -> str:
        return f"{super().name_prefix} Domestic Hot Water {self.dhw_index}"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_domestic_hot_water_{self.dhw_index}"

    @property
    def domestic_hot_water(self) -> DomesticHotWater:
        return self.system.domestic_hot_water[self.dhw_index]


class DomesticHotWaterTankTemperatureSensor(
    BaseDomesticHotWater, BaseTemperatureEntity
):
    @property
    def name_suffix(self):
        return "Tank Temperature"

    @property
    def id_suffix(self) -> str:
        return "tank_temperature"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_dhw_temperature


class DomesticHotWaterSetPointSensor(BaseDomesticHotWater, BaseTemperatureEntity):
    @property
    def name_suffix(self):
        return "Setpoint"

    @property
    def id_suffix(self) -> str:
        return "set_point"

    @property
    def native_value(self) -> float | None:
        return self.domestic_hot_water.tapping_setpoint


class DomesticHotWaterOperationModeSensor(BaseDomesticHotWater, SensorEntity):
    @property
    def name_suffix(self):
        return "Operation Mode"

    @property
    def id_suffix(self) -> str:
        return "operation_mode"

    @property
    def native_value(self):
        return self.domestic_hot_water.operation_mode_dhw.display_value

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.DIAGNOSTIC


class DomesticHotWaterCurrentSpecialFunctionSensor(BaseDomesticHotWater, SensorEntity):
    @property
    def name_suffix(self):
        return "Current Special Function"

    @property
    def id_suffix(self) -> str:
        return "current_special_function"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_special_function.display_value

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.DIAGNOSTIC


class DomesticHotWaterBoostSwitch(BaseDomesticHotWater, SwitchEntity):
    @property
    def name_suffix(self):
        return "Boost"

    @property
    def id_suffix(self) -> str:
        return "boost_switch"

    @property
    def is_on(self):
        return (
            self.domestic_hot_water.current_special_function
            == DHWCurrentSpecialFunction.CYLINDER_BOOST
        )

    async def async_turn_on(self, **kwargs):
        await self.coordinator.api.boost_domestic_hot_water(
            self.domestic_hot_water,
        )
        await self.coordinator.async_request_refresh_delayed()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.api.cancel_hot_water_boost(
            self.domestic_hot_water,
        )
        await self.coordinator.async_request_refresh_delayed()


class DomesticHotWaterEntity(BaseDomesticHotWater, WaterHeaterEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = [d.display_value for d in DHWOperationMode] + [
        DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value
    ]

    @property
    def id_suffix(self) -> str:
        return "base"

    @property
    def name_suffix(self) -> str:
        return "Heating"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program_dhw": self.domestic_hot_water.time_program_dhw,
            "time_program_circulation_pump": self.domestic_hot_water.time_program_circulation_pump,
        }
        return attr | prepare_field_value_for_dict(self.domestic_hot_water.extra_fields)

    @property
    def supported_features(self) -> WaterHeaterEntityFeature:
        return (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )

    @property
    def target_temperature(self) -> float | None:
        return self.domestic_hot_water.tapping_setpoint

    @property
    def current_temperature(self) -> float | None:
        if isinstance(self.domestic_hot_water.current_dhw_temperature, float):
            return round(self.domestic_hot_water.current_dhw_temperature, 1)
        else:
            return None

    @property
    def min_temp(self) -> float:
        return self.domestic_hot_water.min_setpoint

    @property
    def max_temp(self) -> float:
        return self.domestic_hot_water.max_setpoint

    @property
    def current_operation(self) -> str:
        if (
            self.domestic_hot_water.current_special_function
            == DHWCurrentSpecialFunction.CYLINDER_BOOST
        ):
            return str(DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value)
        return str(self.domestic_hot_water.operation_mode_dhw.display_value)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if isinstance(target_temp, (int, float)):
            await self.coordinator.api.set_domestic_hot_water_temperature(
                self.domestic_hot_water, int(target_temp)
            )

    async def async_set_operation_mode(
        self, operation_mode: str, **kwargs: Any
    ) -> None:
        enum_value = operation_mode.upper().replace(" ", "_")
        if enum_value == str(DHWCurrentSpecialFunction.CYLINDER_BOOST):
            # Boost was requested
            await self.coordinator.api.boost_domestic_hot_water(
                self.domestic_hot_water,
            )
        elif (
            self.domestic_hot_water.current_special_function
            == DHWCurrentSpecialFunction.CYLINDER_BOOST
        ):
            # Something other than boost was requested, but boost mode is currently active
            await self.coordinator.api.cancel_hot_water_boost(
                self.domestic_hot_water,
            )
            if enum_value != self.domestic_hot_water.operation_mode_dhw:
                await self.coordinator.api.set_domestic_hot_water_operation_mode(
                    self.domestic_hot_water,
                    DHWOperationMode(enum_value),
                )
        else:
            await self.coordinator.api.set_domestic_hot_water_operation_mode(
                self.domestic_hot_water,
                DHWOperationMode(enum_value),
            )
        await self.coordinator.async_request_refresh_delayed()

    async def set_dhw_time_program(self, **kwargs):
        time_program = DHWTimeProgram.from_api(**kwargs.get("time_program"))
        await self.coordinator.api.set_domestic_hot_water_time_program(
            self.domestic_hot_water, time_program
        )
        await self.coordinator.async_request_refresh_delayed()

    async def set_dhw_circulation_time_program(self, **kwargs):
        time_program = DHWTimeProgram.from_api(**kwargs.get("time_program"))
        await self.coordinator.api.set_domestic_hot_water_circulation_time_program(
            self.domestic_hot_water, time_program
        )
        await self.coordinator.async_request_refresh_delayed()
