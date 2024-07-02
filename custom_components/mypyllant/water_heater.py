import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from myPyllant.models import (
    DHWTimeProgram,
    DomesticHotWater,
    System,
)
from myPyllant.enums import (
    DHWCurrentSpecialFunction,
    DHWOperationMode,
    DHWOperationModeVRC700,
    DHWCurrentSpecialFunctionVRC700,
)
from myPyllant.utils import prepare_field_value_for_dict

from . import SystemCoordinator
from .const import (
    DOMAIN,
    SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM,
    SERVICE_SET_DHW_TIME_PROGRAM,
)
from .utils import EntityList

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping water heater")
        return

    dhws: EntityList[WaterHeaterEntity] = EntityList()

    for index, system in enumerate(coordinator.data):
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            data_key = f"dhw_{index}_{dhw_index}"
            if data_key not in hass.data[DOMAIN][config.entry_id]:
                hass.data[DOMAIN][config.entry_id][data_key] = {}
            dhws.append(
                lambda: DomesticHotWaterEntity(
                    index,
                    dhw_index,
                    coordinator,
                    hass.data[DOMAIN][config.entry_id][data_key],
                )
            )

    async_add_entities(dhws)  # type: ignore

    if len(dhws) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up water heater entity services for %s", platform)
        platform.async_register_entity_service(
            SERVICE_SET_DHW_TIME_PROGRAM,
            {
                vol.Required("time_program"): vol.All(dict),
            },
            "set_dhw_time_program",
        )
        platform.async_register_entity_service(
            SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM,
            {
                vol.Required("time_program"): vol.All(dict),
            },
            "set_dhw_circulation_time_program",
        )


class DomesticHotWaterEntity(CoordinatorEntity, WaterHeaterEntity):
    coordinator: SystemCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, system_index, dhw_index, coordinator, data) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.system_index = system_index
        self.dhw_index = dhw_index
        self.data = data
        self.data["last_active_operation_mode"] = (
            self.current_operation
            if self.current_operation != DHWOperationMode.OFF
            else DHWOperationMode.TIME_CONTROLLED
        )
        _LOGGER.debug(
            "Saving last active DHW operation %s",
            self.data["last_active_operation_mode"],
        )

    async def async_update(self) -> None:
        """
        Save last active HVAC mode after update, so it can be restored in turn_on
        """
        await super().async_update()

        if self.enabled and self.current_operation != DHWOperationMode.OFF:
            _LOGGER.debug(
                "Saving last active DHW operation mode %s", self.current_operation
            )
            self.data["last_active_operation_mode"] = self.current_operation

    @property
    def operation_list(self):
        if self.domestic_hot_water.control_identifier.is_vrc700:
            return [d.display_value for d in DHWOperationModeVRC700] + [
                DHWCurrentSpecialFunctionVRC700.CYLINDER_BOOST.display_value
            ]
        else:
            return [d.display_value for d in DHWOperationMode] + [
                DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value
            ]

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def domestic_hot_water(self) -> DomesticHotWater:
        return self.system.domestic_hot_water[self.dhw_index]

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} Domestic Hot Water {self.dhw_index}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_domestic_hot_water_{self.dhw_index}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.id_infix,
                )
            },
            name=self.name,
            manufacturer=self.system.brand_name,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "time_program_dhw": self.domestic_hot_water.time_program_dhw,
            "time_program_circulation_pump": self.domestic_hot_water.time_program_circulation_pump,
        }
        return attr | prepare_field_value_for_dict(self.domestic_hot_water.extra_fields)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_base"

    @property
    def name(self) -> str:
        return self.name_prefix

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
        if self.domestic_hot_water.is_cylinder_boosting:
            return str(DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value)
        return str(self.domestic_hot_water.operation_mode_dhw.display_value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_set_operation_mode(self.data["last_active_operation_mode"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_set_operation_mode(DHWOperationMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if isinstance(target_temp, (int, float)):
            await self.coordinator.api.set_domestic_hot_water_temperature(
                self.domestic_hot_water, int(target_temp)
            )
            await self.coordinator.async_request_refresh_delayed()

    async def async_set_operation_mode(
        self, operation_mode: str, **kwargs: Any
    ) -> None:
        enum_value = operation_mode.upper().replace(" ", "_")
        if self.domestic_hot_water.control_identifier.is_vrc700:
            enum_class = DHWOperationModeVRC700  # type: ignore
        else:
            enum_class = DHWOperationMode  # type: ignore

        if enum_value in [
            DHWCurrentSpecialFunction.CYLINDER_BOOST,
            DHWCurrentSpecialFunctionVRC700.CYLINDER_BOOST,
        ]:
            # Boost was requested
            await self.coordinator.api.boost_domestic_hot_water(
                self.domestic_hot_water,
            )
        elif self.domestic_hot_water.is_cylinder_boosting:
            # Something other than boost was requested, but boost mode is currently active
            await self.coordinator.api.cancel_hot_water_boost(
                self.domestic_hot_water,
            )
            if enum_value != self.domestic_hot_water.operation_mode_dhw:
                await self.coordinator.api.set_domestic_hot_water_operation_mode(
                    self.domestic_hot_water,
                    enum_class(enum_value),
                )
        else:
            await self.coordinator.api.set_domestic_hot_water_operation_mode(
                self.domestic_hot_water,
                enum_class(enum_value),
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
