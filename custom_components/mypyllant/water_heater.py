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
    DHWCurrentSpecialFunction,
    DHWOperationMode,
    DHWTimeProgram,
    DomesticHotWater,
    System,
)

from . import SystemCoordinator
from .const import (
    DOMAIN,
    SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM,
    SERVICE_SET_DHW_TIME_PROGRAM,
)

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

    dhws: list[WaterHeaterEntity] = []

    for index, system in enumerate(coordinator.data):
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            dhws.append(DomesticHotWaterEntity(index, dhw_index, coordinator))

    async_add_entities(dhws)
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
    _attr_operation_list = [d.display_value for d in DHWOperationMode] + [
        DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value
    ]

    def __init__(self, system_index, dhw_index, coordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.system_index = system_index
        self.dhw_index = dhw_index
        self.entity_id = f"{DOMAIN}.domestic_hot_water_{dhw_index}"

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def domestic_hot_water(self) -> DomesticHotWater:
        return self.system.domestic_hot_water[self.dhw_index]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (DOMAIN, f"domestic_hot_water{self.domestic_hot_water.index}")
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
        return attr

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_domestic_hot_water_{self.dhw_index}"

    @property
    def name(self) -> str:
        return f"Domestic Hot Water {self.dhw_index}"

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
