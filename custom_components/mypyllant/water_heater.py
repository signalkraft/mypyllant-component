import logging
from typing import Any, List

from homeassistant.components.water_heater import (
    UnitOfTemperature,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from . import MyPyllantUpdateCoordinator
from myPyllant.models import System, DomesticHotWater

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: MyPyllantUpdateCoordinator = hass.data[DOMAIN][config.entry_id][
        "coordinator"
    ]

    dhws: List[WaterHeaterEntity] = []

    for index, system in enumerate(coordinator.data):
        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            dhws.append(DomesticHotWaterEntity(index, dhw_index, coordinator))

    async_add_entities(dhws)


class DomesticHotWaterEntity(CoordinatorEntity, WaterHeaterEntity):
    coordinator: MyPyllantUpdateCoordinator
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

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
                (DOMAIN, "domestic_hot_water", str(self.domestic_hot_water.index))
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
        return WaterHeaterEntityFeature.TARGET_TEMPERATURE

    @property
    def available(self) -> bool:
        return self.system.status["online"]

    @property
    def target_temperature(self) -> float:
        return self.domestic_hot_water.set_point

    @property
    def current_temperature(self) -> float:
        return self.domestic_hot_water.current_dhw_tank_temperature

    @property
    def min_temp(self) -> float:
        self.domestic_hot_water.min_set_point

    @property
    def max_temp(self) -> float:
        self.domestic_hot_water.max_set_point

    @property
    def current_operation(self) -> str:
        return self.domestic_hot_water.operation_mode

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        await self.coordinator.api.set_domestic_hot_water_temperature(
            self.domestic_hot_water, int(target_temp)
        )
