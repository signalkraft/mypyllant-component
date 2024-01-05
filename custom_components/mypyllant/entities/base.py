from abc import ABC, abstractmethod
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from custom_components.mypyllant import SystemCoordinator
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfPressure

from myPyllant.models import System, DeviceData

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.coordinator import DailyDataCoordinator


class Base:
    @property
    @abstractmethod
    def id_infix(self) -> str:
        pass

    @property
    @abstractmethod
    def name_prefix(self) -> str:
        pass

    @property
    @abstractmethod
    def id_suffix(self) -> str:
        pass

    @property
    @abstractmethod
    def name_suffix(self) -> str:
        pass

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_{self.id_suffix}"

    @property
    def name(self):
        return f"{self.name_prefix} {self.name_suffix}"


class BaseSystemCoordinator(Base, CoordinatorEntity):
    coordinator: SystemCoordinator
    system_index: int

    def __init__(self, system_index: int, coordinator: SystemCoordinator) -> None:
        super().__init__(coordinator)
        self.system_index = system_index

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}"

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature}"

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )


class BaseSystemDailyCoordinator(Base, CoordinatorEntity):
    coordinator: DailyDataCoordinator
    system_index: int

    def __init__(self, system_index: int, coordinator: DailyDataCoordinator) -> None:
        super().__init__(coordinator)
        self.system_index = system_index

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}"

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature}"

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]["system"]

    @property
    def devices(self) -> list[list[DeviceData]]:
        return self.coordinator.data[self.system_index]["devices_data"]

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
        )


class BaseTemperatureEntity(SensorEntity, ABC):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    @abstractmethod
    def native_value(self) -> float | None:
        pass


class BasePressureEntity(SensorEntity, ABC):
    _attr_native_unit_of_measurement = UnitOfPressure.BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    @abstractmethod
    def native_value(self) -> float | None:
        pass


class BaseHumidityEntity(SensorEntity, ABC):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    @abstractmethod
    def native_value(self) -> float | None:
        pass


class BaseEfficiencyEntity(SensorEntity, ABC):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    @abstractmethod
    def device_data_list(self) -> list[DeviceData]:
        pass

    @property
    def energy_consumed(self) -> float:
        """
        Returns total consumed electrical energy for the current day
        """
        return sum(
            [
                v.data[-1].value
                for v in self.device_data_list
                if len(v.data)
                and v.data[-1].value
                and v.energy_type == "CONSUMED_ELECTRICAL_ENERGY"
            ]
        )

    @property
    def heat_energy_generated(self) -> float:
        """
        Returns total generated heating energy for the current day
        """
        return sum(
            [
                v.data[-1].value
                for v in self.device_data_list
                if len(v.data)
                and v.data[-1].value
                and v.energy_type == "HEAT_GENERATED"
            ]
        )

    @property
    def native_value(self) -> float | None:
        if self.energy_consumed is not None and self.energy_consumed > 0:
            return round(self.heat_energy_generated / self.energy_consumed, 1)
        else:
            return None
