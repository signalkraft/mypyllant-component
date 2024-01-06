from typing import Any, Mapping
from custom_components.mypyllant.coordinator import DeviceDataCoordinator
from custom_components.mypyllant.entities.base import (
    BaseDeviceDataCoordinatorEntity,
    BaseEfficiencyEntity,
    BasePressureEntity,
    BaseSystemCoordinatorEntity,
    BaseTemperatureEntity,
)

from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorEntity

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from myPyllant.models import DeviceData


class BaseSystem(BaseSystemCoordinatorEntity):
    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_home"

    @property
    def name_prefix(self) -> str:
        return f"{super().name_prefix}"

    @property
    def device_info(self):
        device = super().device_info
        device.update(
            model=self.system.home.nomenclature,
            sw_version=self.system.home.firmware_version,
        )
        return device


class SystemOutdoorTemperatureSensor(BaseSystem, BaseTemperatureEntity):
    @property
    def id_suffix(self) -> str:
        return "outdoor_temperature"

    @property
    def name_suffix(self):
        return "Outdoor Temperature"

    @property
    def native_value(self):
        if self.system.outdoor_temperature is not None:
            return round(self.system.outdoor_temperature, 1)
        else:
            return None


class SystemWaterPressureSensor(BaseSystem, BasePressureEntity):
    @property
    def id_suffix(self) -> str:
        return "water_pressure"

    @property
    def name_suffix(self):
        return "System Water Pressure"

    @property
    def native_value(self):
        if self.system.water_pressure is not None:
            return round(self.system.water_pressure, 1)
        else:
            return None

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class HomeEntity(BaseSystem, SensorEntity):
    @property
    def id_suffix(self) -> str:
        return "base"

    @property
    def name_suffix(self):
        return "Firmware Version"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self.system.home.extra_fields | self.system.extra_fields

    @property
    def native_value(self):
        return self.system.home.firmware_version


class ControlError(BaseSystem, BinarySensorEntity):
    @property
    def id_suffix(self) -> str:
        return "control_error"

    @property
    def name_suffix(self) -> str:
        return "Trouble Codes"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "diagnostic_trouble_codes": self.system.diagnostic_trouble_codes,
        }
        return attr

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        return self.system.has_diagnostic_trouble_codes

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.PROBLEM


class ControlOnline(BaseSystem, BinarySensorEntity):
    @property
    def id_suffix(self) -> str:
        return "control_online"

    @property
    def name_suffix(self) -> str:
        return "Online Status"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.system.connected is True

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.CONNECTIVITY


class FirmwareUpdateRequired(BaseSystem, BinarySensorEntity):
    @property
    def id_suffix(self) -> str:
        return "firmware_update_required"

    @property
    def name_suffix(self) -> str:
        return "Firmware Update Required"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        return self.system.home.firmware.get("update_required", None)

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.UPDATE


class FirmwareUpdateEnabled(BaseSystem, BinarySensorEntity):
    @property
    def id_suffix(self) -> str:
        return "firmware_update_enabled"

    @property
    def name_suffix(self) -> str:
        return "Firmware Update Enabled"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        return self.system.home.firmware.get("update_enabled", None)


class SystemEfficiencySensor(BaseDeviceDataCoordinatorEntity, BaseEfficiencyEntity):
    def __init__(self, system_index: int, coordinator: DeviceDataCoordinator) -> None:
        super().__init__(system_index, coordinator)

    @property
    def device_data_list(self) -> list[DeviceData]:
        return [item for row in self.devices for item in row]

    @property
    def name_suffix(self):
        return "Heating Energy Efficiency"

    @property
    def id_suffix(self) -> str:
        return "heating_energy_efficiency"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_home"

    @property
    def name_prefix(self) -> str:
        return f"{super().name_prefix}"
