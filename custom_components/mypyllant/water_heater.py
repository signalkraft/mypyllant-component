import logging
from typing import Any, List

from myPyllant.models import (
    DHWCurrentSpecialFunction,
    DHWOperationMode,
    DomesticHotWater,
    System,
)

from homeassistant.components.water_heater import (
    UnitOfTemperature,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SystemCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]

    dhws: list[WaterHeaterEntity] = []

    for index, system in enumerate(coordinator.data):
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            dhws.append(DomesticHotWaterEntity(index, dhw_index, coordinator))

    async_add_entities(dhws)


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
            manufacturer="Vaillant",
        )

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
    def available(self) -> bool | None:
        return self.system.status_online

    @property
    def target_temperature(self) -> float:
        return self.domestic_hot_water.set_point

    @property
    def current_temperature(self) -> float:
        return self.domestic_hot_water.current_dhw_tank_temperature

    @property
    def min_temp(self) -> float:
        return self.domestic_hot_water.min_set_point

    @property
    def max_temp(self) -> float:
        return self.domestic_hot_water.max_set_point

    @property
    def current_operation(self) -> str:
        if (
            self.domestic_hot_water.current_special_function
            == DHWCurrentSpecialFunction.CYLINDER_BOOST
        ):
            return str(DHWCurrentSpecialFunction.CYLINDER_BOOST.display_value)
        return str(self.domestic_hot_water.operation_mode.display_value)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        target_temp = kwargs.get(ATTR_TEMPERATURE)
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
            if enum_value != self.domestic_hot_water.operation_mode:
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
