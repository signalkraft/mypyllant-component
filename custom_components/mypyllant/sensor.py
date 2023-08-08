from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ENERGY_WATT_HOUR, PERCENTAGE, PRESSURE_BAR, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from myPyllant.models import (
    Circuit,
    Device,
    DeviceData,
    DeviceDataBucket,
    DomesticHotWater,
    System,
    Zone,
)

from . import DailyDataCoordinator, SystemCoordinator
from .const import DOMAIN
from .utils import get_system_sensor_unique_id

_LOGGER = logging.getLogger(__name__)

DATA_UNIT_MAP = {
    "CONSUMED_ELECTRICAL_ENERGY": ENERGY_WATT_HOUR,
    "EARNED_ENVIRONMENT_ENERGY": ENERGY_WATT_HOUR,
    "HEAT_GENERATED": ENERGY_WATT_HOUR,
    "CONSUMED_PRIMARY_ENERGY": ENERGY_WATT_HOUR,
}


async def create_system_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> list[SensorEntity]:
    system_coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not system_coordinator.data:
        _LOGGER.warning("No system data, skipping sensors")
        return []

    sensors: list[SensorEntity] = []
    _LOGGER.debug(f"Creating system sensors for {system_coordinator.data}")
    for index, system in enumerate(system_coordinator.data):
        if system.outdoor_temperature is not None:
            sensors.append(SystemOutdoorTemperatureSensor(index, system_coordinator))
        if system.water_pressure is not None:
            sensors.append(SystemWaterPressureSensor(index, system_coordinator))
        # TODO find replacement value
        # if system.mode is not None:
        #     sensors.append(SystemModeSensor(index, system_coordinator))

        for device_index, device in enumerate(system.devices):
            _LOGGER.debug(f"Creating SystemDevice sensors for {device}")

            if "water_pressure" in device.operational_data:
                sensors.append(
                    SystemDeviceWaterPressureSensor(
                        index, device_index, system_coordinator
                    )
                )

        for zone_index, zone in enumerate(system.zones):
            _LOGGER.debug(f"Creating Zone sensors for {zone}")
            sensors.append(
                ZoneDesiredRoomTemperatureSetpointSensor(
                    index, zone_index, system_coordinator
                )
            )
            if zone.current_room_temperature is not None:
                sensors.append(
                    ZoneCurrentRoomTemperatureSensor(
                        index, zone_index, system_coordinator
                    )
                )
            if zone.current_room_humidity is not None:
                sensors.append(
                    ZoneHumiditySensor(index, zone_index, system_coordinator)
                )
            sensors.append(
                ZoneHeatingOperatingModeSensor(index, zone_index, system_coordinator)
            )
            sensors.append(
                ZoneHeatingStateSensor(index, zone_index, system_coordinator)
            )
            sensors.append(
                ZoneCurrentSpecialFunctionSensor(index, zone_index, system_coordinator)
            )

        for circuit_index, circuit in enumerate(system.circuits):
            _LOGGER.debug(f"Creating Circuit sensors for {circuit}")
            sensors.append(CircuitStateSensor(index, circuit_index, system_coordinator))
            if circuit.current_circuit_flow_temperature is not None:
                sensors.append(
                    CircuitFlowTemperatureSensor(
                        index, circuit_index, system_coordinator
                    )
                )
            if circuit.heating_curve is not None:
                sensors.append(
                    CircuitHeatingCurveSensor(index, circuit_index, system_coordinator)
                )
            if circuit.min_flow_temperature_setpoint is not None:
                sensors.append(
                    CircuitMinFlowTemperatureSetpointSensor(
                        index, circuit_index, system_coordinator
                    )
                )

        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            _LOGGER.debug(f"Creating Domestic Hot Water sensors for {dhw}")
            if dhw.current_dhw_temperature:
                sensors.append(
                    DomesticHotWaterTankTemperatureSensor(
                        index, dhw_index, system_coordinator
                    )
                )
            sensors.append(
                DomesticHotWaterSetPointSensor(index, dhw_index, system_coordinator)
            )
            sensors.append(
                DomesticHotWaterOperationModeSensor(
                    index, dhw_index, system_coordinator
                )
            )
            sensors.append(
                DomesticHotWaterCurrentSpecialFunctionSensor(
                    index, dhw_index, system_coordinator
                )
            )
    return sensors


async def create_daily_data_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> list[SensorEntity]:
    daily_data_coordinator: DailyDataCoordinator = hass.data[DOMAIN][config.entry_id][
        "daily_data_coordinator"
    ]

    _LOGGER.debug(f"Daily data: {daily_data_coordinator.data}")

    if not daily_data_coordinator.data:
        _LOGGER.warning("No daily data, skipping sensors")
        return []

    sensors: list[SensorEntity] = []
    for system_id in daily_data_coordinator.data.keys():
        _LOGGER.debug(f"Creating efficiency sensor for System {system_id}")
        sensors.append(EfficiencySensor(system_id, daily_data_coordinator))
        for da_index, _ in enumerate(daily_data_coordinator.data[system_id]):
            sensors.append(DataSensor(system_id, da_index, daily_data_coordinator))

    return sensors


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(await create_system_sensors(hass, config))
    async_add_entities(await create_daily_data_sensors(hass, config))


class SystemSensor(CoordinatorEntity, SensorEntity):
    coordinator: SystemCoordinator

    def __init__(self, index: int, coordinator: SystemCoordinator) -> None:
        super().__init__(coordinator)
        self.index = index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.index]

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, f"device{get_system_sensor_unique_id(self.system)}")
            }
        }


class SystemOutdoorTemperatureSensor(SystemSensor):
    _attr_name = "Outdoor Temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self.system.outdoor_temperature:
            return round(self.system.outdoor_temperature, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_outdoor_temperature_{self.index}"


class SystemWaterPressureSensor(SystemSensor):
    _attr_name = "System Water Pressure"
    _attr_native_unit_of_measurement = PRESSURE_BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self.system.water_pressure:
            return round(self.system.water_pressure, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_water_pressure_{self.index}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class ZoneEntity(CoordinatorEntity, SensorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, zone_index: int, coordinator: SystemCoordinator
    ) -> None:
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
        return {"identifiers": {(DOMAIN, f"zone{self.zone.index}")}}

    @property
    def available(self) -> bool | None:
        return self.zone.is_active


class ZoneDesiredRoomTemperatureSetpointSensor(ZoneEntity):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Desired Temperature in {self.zone.name}"

    @property
    def native_value(self):
        if self.zone.desired_room_temperature_setpoint_heating:
            return self.zone.desired_room_temperature_setpoint_heating
        elif self.zone.desired_room_temperature_setpoint_cooling:
            return self.zone.desired_room_temperature_setpoint_cooling
        else:
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
        return round(self.zone.current_room_temperature, 1)

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
        return self.zone.current_room_humidity

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_zone_humidity_{self.system_index}_{self.zone_index}"


class ZoneHeatingOperatingModeSensor(ZoneEntity):
    @property
    def name(self):
        return f"Heating Operating Mode in {self.zone.name}"

    @property
    def native_value(self):
        return self.zone.heating.operation_mode_heating.display_value

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
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, circuit_index: int, coordinator: SystemCoordinator
    ) -> None:
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
        return {"identifiers": {(DOMAIN, f"circuit{self.circuit.index}")}}


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
        if self.circuit.heating_curve:
            return round(self.circuit.heating_curve, 2)
        else:
            return None

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return (
            f"{DOMAIN}_circuit_heating_curve_{self.system_index}_{self.circuit_index}"
        )


class DomesticHotWaterSensor(CoordinatorEntity, SensorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, dhw_index: int, coordinator: SystemCoordinator
    ) -> None:
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
                (DOMAIN, f"domestic_hot_water{self.domestic_hot_water.index}")
            }
        }


class DomesticHotWaterTankTemperatureSensor(DomesticHotWaterSensor):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Tank Temperature Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_dhw_temperature

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_tank_temperature_{self.system_index}_{self.dhw_index}"


class DomesticHotWaterSetPointSensor(DomesticHotWaterSensor):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Setpoint Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self) -> float | None:
        return self.domestic_hot_water.tapping_setpoint

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_set_point_{self.system_index}_{self.dhw_index}"


class DomesticHotWaterOperationModeSensor(DomesticHotWaterSensor):
    @property
    def name(self):
        return f"Operation Mode Domestic Hot Water {self.domestic_hot_water.index}"

    @property
    def native_value(self):
        return self.domestic_hot_water.operation_mode_dhw.display_value

    @property
    def entity_category(self) -> EntityCategory:
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
        return self.domestic_hot_water.current_special_function.display_value

    @property
    def entity_category(self) -> EntityCategory:
        return EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_dhw_current_special_function_{self.system_index}_{self.dhw_index}"


class DataSensor(CoordinatorEntity, SensorEntity):
    coordinator: DailyDataCoordinator
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, system_id: str, da_index: int, coordinator: DailyDataCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_id = system_id
        self.da_index = da_index
        if self.device_data.energy_type in DATA_UNIT_MAP:
            self._attr_native_unit_of_measurement = DATA_UNIT_MAP[
                self.device_data.energy_type
            ]
        self._attr_device_class = SensorDeviceClass.ENERGY
        _LOGGER.debug(
            f"Finishing init of {self.name} = {self.native_value} and unique id {self.unique_id}"
        )

    @property
    def name(self):
        name = self.device.name_display
        om = self.device_data.operation_mode.replace("_", " ").title()
        et = self.device_data.energy_type.replace("_", " ").title()
        return f"{name} {et} {om}"

    @property
    def device_data(self) -> DeviceData:
        return self.coordinator.data[self.system_id][self.da_index]

    @property
    def device(self) -> Device | None:
        return self.device_data.device

    @property
    def data_bucket(self) -> DeviceDataBucket | None:
        data = [d for d in self.device_data.data if d.value is not None]
        if len(data) > 0:
            return data[-1]
        else:
            return None

    @property
    def unique_id(self) -> str:
        dt = self.device.device_type.lower() if self.device else "unknown"
        om = self.device_data.operation_mode.lower()
        et = (
            self.device_data.energy_type.lower()
            if self.device_data.energy_type
            else "unknown"
        )
        return f"{DOMAIN}_{dt}_{om}_{et}_{self.da_index}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"device{self.device.device_uuid}")},
            name=self.device.name_display,
            manufacturer="Vaillant",
            model=self.device.product_name_display,
        )

    @property
    def native_value(self):
        return self.data_bucket.value if self.data_bucket else None

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
        _LOGGER.debug(
            f"Updated DataSensor {self.unique_id} = {self.native_value} last reset on {self.last_reset}, "
            f"from data {self.device_data.data}"
        )


class EfficiencySensor(CoordinatorEntity, SensorEntity):
    coordinator: DailyDataCoordinator
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_name = "Heating Energy Efficiency"

    def __init__(self, system_id: str, coordinator: DailyDataCoordinator) -> None:
        super().__init__(coordinator)
        self.system_id = system_id

    @property
    def device_data_list(self) -> list[DeviceData]:
        return self.coordinator.data[self.system_id]

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
    def unique_id(self) -> str:
        return f"{DOMAIN}_heating_energy_efficiency_{self.system_id}"

    @property
    def device_info(self):
        if len(self.device_data_list) > 0:
            return {
                "identifiers": {
                    (DOMAIN, f"device{self.device_data_list[0].device.device_uuid}")
                }
            }
        else:
            return None

    @property
    def native_value(self) -> float | None:
        if self.energy_consumed:
            return round(self.heat_energy_generated / self.energy_consumed, 1)
        else:
            return None


class SystemDeviceSensor(CoordinatorEntity, SensorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, device_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.device_index = device_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def device(self) -> Device:
        return self.system.devices[self.device_index]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, f"system{self.system.id}")}}


class SystemDeviceWaterPressureSensor(SystemDeviceSensor):
    _attr_native_unit_of_measurement = PRESSURE_BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"Water Pressure {self.device.name}"

    @property
    def native_value(self):
        return self.device.operational_data.get("water_pressure", {}).get("value")

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_water_pressure_{self.device.device_uuid}"

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC
