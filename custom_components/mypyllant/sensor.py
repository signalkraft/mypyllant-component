from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE, PRESSURE_BAR, ENERGY_WATT_HOUR
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from myPyllant.models import System, Zone, Circuit, DomesticHotWater, Device, DeviceData, DeviceDataBucket


import logging

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


DATA_UNIT_MAP = {
    "CONSUMED_ELECTRICAL_ENERGY": ENERGY_WATT_HOUR,
    "EARNED_ENVIRONMENT_ENERGY": ENERGY_WATT_HOUR,
    "HEAT_GENERATED": ENERGY_WATT_HOUR
}


DATA_DEVICE_CLASS_MAP = {
    "CONSUMED_ELECTRICAL_ENERGY": SensorDeviceClass.ENERGY,
    "EARNED_ENVIRONMENT_ENERGY": SensorDeviceClass.ENERGY,
    "HEAT_GENERATED": SensorDeviceClass.ENERGY,
}


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    system_coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    data_coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config.entry_id][
        "data_coordinator"
    ]
    sensors: list[SensorEntity] = []
    for index, system in enumerate(system_coordinator.data):
        sensors.append(SystemOutdoorTemperatureSensor(index, system_coordinator))
        sensors.append(SystemWaterPressureSensor(index, system_coordinator))
        sensors.append(SystemModeSensor(index, system_coordinator))
        for zone_index, _ in enumerate(system.zones):
            sensors.append(
                ZoneDesiredRoomTemperatureSetpointSensor(index, zone_index, system_coordinator)
            )
            sensors.append(
                ZoneCurrentRoomTemperatureSensor(index, zone_index, system_coordinator)
            )
            sensors.append(ZoneHumiditySensor(index, zone_index, system_coordinator))
            sensors.append(
                ZoneHeatingOperatingModeSensor(index, zone_index, system_coordinator)
            )
            sensors.append(ZoneHeatingStateSensor(index, zone_index, system_coordinator))
            sensors.append(
                ZoneCurrentSpecialFunctionSensor(index, zone_index, system_coordinator)
            )

        for circuit_index, _ in enumerate(system.circuits):
            sensors.append(
                CircuitFlowTemperatureSensor(index, circuit_index, system_coordinator)
            )
            sensors.append(CircuitHeatingCurveSensor(index, circuit_index, system_coordinator))
            sensors.append(
                CircuitMinFlowTemperatureSetpointSensor(
                    index, circuit_index, system_coordinator
                )
            )
            sensors.append(CircuitStateSensor(index, circuit_index, system_coordinator))
        for dhw_index, _ in enumerate(system.domestic_hot_water):
            sensors.append(
                DomesticHotWaterTankTemperatureSensor(index, dhw_index, system_coordinator)
            )
            sensors.append(
                DomesticHotWaterOperationModeSensor(index, dhw_index, system_coordinator)
            )
            sensors.append(
                DomesticHotWaterCurrentSpecialFunctionSensor(
                    index, dhw_index, system_coordinator
                )
            )
    for device_index, device_data_list in enumerate(data_coordinator.data['device_data']):
        for da_index, _ in enumerate(device_data_list):
            sensors.append(DataSensor(device_index, da_index, data_coordinator))

    async_add_entities(sensors)


class SystemSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, index, coordinator) -> None:
        super().__init__(coordinator)
        self.index = index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.index]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, "system", self.system.id)}}

    @property
    def available(self) -> bool:
        return self.system.status["online"]


class SystemOutdoorTemperatureSensor(SystemSensor):
    _attr_name = "Outdoor Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return round(self.coordinator.data[self.index].outdoor_temperature, 2)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_outdoor_temperature_{self.index}"


class SystemWaterPressureSensor(SystemSensor):
    _attr_name = "Water Pressure"
    _attr_native_unit_of_measurement = PRESSURE_BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return round(self.system.water_pressure, 1)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_water_pressure_{self.index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class SystemModeSensor(SystemSensor):
    _attr_name = "System Mode"

    @property
    def native_value(self):
        return self.system.system_control_state["control_state"]["general"][
            "system_mode"
        ]

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_system_mode_{self.index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, system_index, zone_index, coordinator) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.zone_index = zone_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def zone(self) -> Zone:
        return self.system.zones[self.zone_index]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, "zone", str(self.zone.index))}}

    @property
    def available(self) -> bool:
        return self.system.status["online"] and self.zone.active


class ZoneDesiredRoomTemperatureSetpointSensor(ZoneEntity):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Desired Temperature in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.desired_room_temperature_setpoint

    @property
    def unique_id(self) -> str:
        return (
            f"{DOMAIN}_zone_desired_temperature_{self.system_index}_{self.zone_index}"
        )


class ZoneCurrentRoomTemperatureSensor(ZoneEntity):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Current Temperature in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.current_room_temperature

    @property
    def unique_id(self) -> str:
        return (
            f"{DOMAIN}_zone_current_temperature_{self.system_index}_{self.zone_index}"
        )


class ZoneHumiditySensor(ZoneEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Humidity in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.humidity

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_zone_humidity_{self.system_index}_{self.zone_index}"


class ZoneHeatingOperatingModeSensor(ZoneEntity):
    @property
    def name(self):
        return f"Heating Operating Mode in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.heating_operation_mode.display_value
    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_zone_heating_operating_mode_{self.system_index}_{self.zone_index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneHeatingStateSensor(ZoneEntity):
    @property
    def name(self):
        return f"Heating State in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.heating_state.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_zone_heating_state_{self.system_index}_{self.zone_index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneCurrentSpecialFunctionSensor(ZoneEntity):
    @property
    def name(self):
        return f"Current Special Function in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.current_special_function.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_zone_current_special_function_{self.system_index}_{self.zone_index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class CircuitSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, system_index, circuit_index, coordinator) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.circuit_index = circuit_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def circuit(self) -> Circuit:
        return self.system.circuits[self.circuit_index]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, "circuit", self.circuit.index)}}

    @property
    def available(self) -> bool:
        return self.system.status["online"]


class CircuitFlowTemperatureSensor(CircuitSensor):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Current Flow Temperature in Circuit {self.circuit.index}"

    @property
    def native_value(self):
        return self.circuit.current_circuit_flow_temperature

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_circuit_flow_temperature_{self.system_index}_{self.circuit_index}"


class CircuitStateSensor(CircuitSensor):
    @property
    def name(self):
        return f"State in Circuit {self.circuit.index}"

    @property
    def native_value(self):
        return self.circuit.circuit_state

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_circuit_state_{self.system_index}_{self.circuit_index}"


class CircuitMinFlowTemperatureSetpointSensor(CircuitSensor):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Min Flow Temperature Setpoint in Circuit {self.circuit.index}"

    @property
    def native_value(self):
        return self.circuit.min_flow_temperature_setpoint

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_circuit_min_flow_temperature_setpoint_{self.system_index}_{self.circuit_index}"


class CircuitHeatingCurveSensor(CircuitSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Heating Curve in Circuit {self.circuit.index}"

    @property
    def native_value(self):
        return self.circuit.heating_curve

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return (
            f"{DOMAIN}_circuit_heating_curve_{self.system_index}_{self.circuit_index}"
        )


class DomesticHotWaterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, system_index, dhw_index, coordinator) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.dhw_index = dhw_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def domestic_hot_water(self) -> DomesticHotWater:
        return self.system.domestic_hot_water[self.dhw_index]

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, "domestic_hot_water", str(self.domestic_hot_water.index))
            }
        }

    @property
    def available(self) -> bool:
        return self.system.status["online"]


class DomesticHotWaterTankTemperatureSensor(DomesticHotWaterSensor):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Tank Temperature Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_dhw_tank_temperature

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_tank_temperature_{self.system_index}_{self.dhw_index}"


class DomesticHotWaterOperationModeSensor(DomesticHotWaterSensor):
    @property
    def name(self):
        return f"Operation Mode Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self):
        return self.domestic_hot_water.operation_mode

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_operation_mode_{self.system_index}_{self.dhw_index}"


class DomesticHotWaterCurrentSpecialFunctionSensor(DomesticHotWaterSensor):
    @property
    def name(self):
        return f"Current Special Function Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_special_function

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_current_special_function_{self.system_index}_{self.dhw_index}"


class DataSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, device_index, da_index, coordinator) -> None:
        super().__init__(coordinator)
        self.device_index = device_index
        self.da_index = da_index
        self._attr_native_unit_of_measurement = DATA_UNIT_MAP[self.device_data.energy_type]
        self._attr_device_class = DATA_DEVICE_CLASS_MAP[self.device_data.energy_type]

    @property
    def name(self):
        name = self.device.name_display
        om = self.device_data.operation_mode.replace('_', ' ').title()
        et = self.device_data.energy_type.replace('_', ' ').title()
        return f"{name} {et} {om}"

    @property
    def device_data(self) -> DeviceData:
        return self.coordinator.data['device_data'][self.device_index][self.da_index]

    @property
    def last_reset(self) -> DeviceData:
        return self.data_bucket.start_date

    @property
    def device(self) -> Device:
        return self.device_data.device

    @property
    def data_bucket(self) -> DeviceDataBucket:
        return self.device_data.data[-1]

    @property
    def unique_id(self) -> str:
        dt = self.device.device_type.lower()
        om = self.device_data.operation_mode.lower()
        et = self.device_data.energy_type.lower()
        return f"{DOMAIN}_{dt}_{om}_{et}_{self.da_index}"

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, "system", self.device.system.id)
            }
        }

    @property
    def native_value(self):
        return self.data_bucket.value
