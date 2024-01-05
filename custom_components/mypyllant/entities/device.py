import logging
from custom_components.mypyllant.coordinator import (
    DailyDataCoordinator,
    SystemCoordinator,
)
from custom_components.mypyllant.entities.base import (
    BaseSystemDailyCoordinator,
    BaseEfficiencyEntity,
    BasePressureEntity,
    BaseSystemCoordinator,
)
from myPyllant.models import Device
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfEnergy
from myPyllant.models import DeviceData, DeviceDataBucket
from homeassistant.core import callback
from typing import cast

DATA_UNIT_MAP = {
    "CONSUMED_ELECTRICAL_ENERGY": UnitOfEnergy.WATT_HOUR,
    "EARNED_ENVIRONMENT_ENERGY": UnitOfEnergy.WATT_HOUR,
    "HEAT_GENERATED": UnitOfEnergy.WATT_HOUR,
    "CONSUMED_PRIMARY_ENERGY": UnitOfEnergy.WATT_HOUR,
    "EARNED_SOLAR_ENERGY": UnitOfEnergy.WATT_HOUR,
}

_LOGGER = logging.getLogger(__name__)


class BaseDevice(BaseSystemCoordinator):
    def __init__(
        self, system_index: int, device_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(system_index, coordinator)
        self.device_index = device_index

    @property
    def name_prefix(self) -> str:
        name_display = f" {self.device.name_display}" if self.device is not None else ""
        return f"{super().name_prefix} Device {self.device_index}{name_display}"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_device_{self.device.device_uuid if self.device is not None else ''}"

    @property
    def device(self) -> Device:
        return self.system.devices[self.device_index]


class SystemDeviceWaterPressureSensor(BaseDevice, BasePressureEntity):
    @property
    def id_suffix(self) -> str:
        return "water_pressure"

    @property
    def name_suffix(self):
        return "Water Pressure"

    @property
    def native_value(self):
        return self.device.operational_data.get("water_pressure", {}).get("value")

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class DataSensor(BaseSystemDailyCoordinator, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        system_index: int,
        de_index: int,
        da_index: int,
        coordinator: DailyDataCoordinator,
    ) -> None:
        super().__init__(system_index, coordinator)
        self.da_index = da_index
        self.de_index = de_index
        if (
            self.device_data is not None
            and self.device_data.energy_type in DATA_UNIT_MAP
        ):
            self._attr_native_unit_of_measurement = DATA_UNIT_MAP[
                self.device_data.energy_type
            ]
        self._attr_device_class = SensorDeviceClass.ENERGY
        _LOGGER.debug(
            "Finishing init of %s = %s and unique id %s",
            self.name,
            self.native_value,
            self.unique_id,
        )

    @property
    def name_suffix(self):
        if self.device_data is None:
            return None
        om = self.device_data.operation_mode.replace("_", " ").title()
        et = (
            self.device_data.energy_type.replace("_", " ").title() + " "
            if self.device_data.energy_type is not None
            else ""
        )
        return f"{et}{om}"

    @property
    def id_suffix(self) -> str:
        if self.device is None:
            return ""
        return f"{self.da_index}"

    @property
    def name_prefix(self) -> str:
        name_display = f" {self.device.name_display}" if self.device is not None else ""
        return f"{super().name_prefix} Device {self.de_index}{name_display}"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_device_{self.device.device_uuid if self.device is not None else ''}"

    @property
    def device_data(self) -> DeviceData | None:
        if len(self.devices) <= self.de_index:
            return None
        if len(self.devices[self.de_index]) <= self.da_index:
            return None
        return self.devices[self.de_index][self.da_index]

    @property
    def device(self) -> Device | None:
        if self.device_data is None:
            return None
        return self.device_data.device

    @property
    def data_bucket(self) -> DeviceDataBucket | None:
        if self.device_data is None:
            return None
        data = [d for d in self.device_data.data if d.value is not None]
        if len(data) > 0:
            return data[-1]
        else:
            return None

    @property
    def device_info(self):
        device = super().device_info

        if self.device is not None:
            device.update(
                manufacturer=self.device.brand_name,
                model=self.device.product_name_display,
            )

        return device

    @property
    def native_value(self):
        return self.data_bucket.value if self.data_bucket else None

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
        _LOGGER.debug(
            "Updated DataSensor %s = %s last reset on %s, from data %s",
            self.unique_id,
            self.native_value,
            self.last_reset,
            self.device_data.data if self.device_data is not None else None,
        )


class DeviceEfficiencySensor(BaseSystemDailyCoordinator, BaseEfficiencyEntity):
    def __init__(
        self, system_index: int, de_index: int | None, coordinator: DailyDataCoordinator
    ) -> None:
        super().__init__(system_index, coordinator)
        self.de_index = de_index

    @property
    def device(self) -> Device:
        return cast(Device, self.device_data_list[0].device)

    @property
    def device_data_list(self) -> list[DeviceData]:
        return [item for row in self.devices for item in row]

    @property
    def name_suffix(self):
        return "Heating Energy Efficiency"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_device_{self.device.device_uuid if self.device is not None else ''}"

    @property
    def id_suffix(self) -> str:
        return "heating_energy_efficiency"

    @property
    def name_prefix(self) -> str:
        name_display = f" {self.device.name_display}" if self.device is not None else ""
        return f"{self.system.home.home_name or self.system.home.nomenclature} Device {self.de_index}{name_display}"
