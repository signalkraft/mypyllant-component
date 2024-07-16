from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from myPyllant.models import (
    Circuit,
    Device,
    DeviceData,
    System,
)

from custom_components.mypyllant.utils import (
    SystemCoordinatorEntity,
    DomesticHotWaterCoordinatorEntity,
    ZoneCoordinatorEntity,
    EntityList,
)
from myPyllant.utils import prepare_field_value_for_dict

from . import DailyDataCoordinator, SystemCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_UNIT_MAP = {
    "CONSUMED_ELECTRICAL_ENERGY": UnitOfEnergy.WATT_HOUR,
    "EARNED_ENVIRONMENT_ENERGY": UnitOfEnergy.WATT_HOUR,
    "HEAT_GENERATED": UnitOfEnergy.WATT_HOUR,
    "CONSUMED_PRIMARY_ENERGY": UnitOfEnergy.WATT_HOUR,
    "EARNED_SOLAR_ENERGY": UnitOfEnergy.WATT_HOUR,
}


async def create_system_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> EntityList[SensorEntity]:
    system_coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not system_coordinator.data:
        _LOGGER.warning("No system data, skipping sensors")
        return EntityList()

    sensors: EntityList[SensorEntity] = EntityList()
    _LOGGER.debug("Creating system sensors for %s", system_coordinator.data)
    for index, system in enumerate(system_coordinator.data):
        if system.outdoor_temperature is not None:
            sensors.append(
                lambda: SystemOutdoorTemperatureSensor(index, system_coordinator)
            )
        if system.water_pressure is not None:
            sensors.append(lambda: SystemWaterPressureSensor(index, system_coordinator))
        if system.cylinder_temperature_sensor_top_dhw is not None:
            sensors.append(
                lambda: SystemTopDHWTemperatureSensor(index, system_coordinator)
            )
        if system.cylinder_temperature_sensor_bottom_dhw is not None:
            sensors.append(
                lambda: SystemBottomDHWTemperatureSensor(index, system_coordinator)
            )
        if system.cylinder_temperature_sensor_top_ch is not None:
            sensors.append(
                lambda: SystemTopCHTemperatureSensor(index, system_coordinator)
            )
        if system.cylinder_temperature_sensor_bottom_ch is not None:
            sensors.append(
                lambda: SystemBottomCHTemperatureSensor(index, system_coordinator)
            )
        sensors.append(lambda: HomeEntity(index, system_coordinator))

        for device_index, device in enumerate(system.devices):
            _LOGGER.debug("Creating SystemDevice sensors for %s", device)

            if "water_pressure" in device.operational_data:
                sensors.append(
                    lambda: SystemDeviceWaterPressureSensor(
                        index, device_index, system_coordinator
                    )
                )
            if device.operation_time is not None:
                sensors.append(
                    lambda: SystemDeviceOperationTimeSensor(
                        index, device_index, system_coordinator
                    )
                )
            if device.on_off_cycles is not None:
                sensors.append(
                    lambda: SystemDeviceOnOffCyclesSensor(
                        index, device_index, system_coordinator
                    )
                )
            if device.current_power is not None:
                sensors.append(
                    lambda: SystemDeviceCurrentPowerSensor(
                        index, device_index, system_coordinator
                    )
                )

        for zone_index, zone in enumerate(system.zones):
            _LOGGER.debug("Creating Zone sensors for %s", zone)
            sensors.append(
                lambda: ZoneDesiredRoomTemperatureSetpointSensor(
                    index, zone_index, system_coordinator
                )
            )
            sensors.append(
                lambda: ZoneDesiredRoomTemperatureSetpointHeatingSensor(
                    index, zone_index, system_coordinator
                )
            )
            sensors.append(
                lambda: ZoneDesiredRoomTemperatureSetpointCoolingSensor(
                    index, zone_index, system_coordinator
                )
            )
            if zone.current_room_temperature is not None:
                sensors.append(
                    lambda: ZoneCurrentRoomTemperatureSensor(
                        index, zone_index, system_coordinator
                    )
                )
            if zone.current_room_humidity is not None:
                sensors.append(
                    lambda: ZoneHumiditySensor(index, zone_index, system_coordinator)
                )
            sensors.append(
                lambda: ZoneHeatingOperatingModeSensor(
                    index, zone_index, system_coordinator
                )
            )
            if zone.heating_state is not None:
                sensors.append(
                    lambda: ZoneHeatingStateSensor(
                        index, zone_index, system_coordinator
                    )
                )
            sensors.append(
                lambda: ZoneCurrentSpecialFunctionSensor(
                    index, zone_index, system_coordinator
                )
            )

        for circuit_index, circuit in enumerate(system.circuits):
            _LOGGER.debug("Creating Circuit sensors for %s", circuit)
            sensors.append(
                lambda: CircuitStateSensor(index, circuit_index, system_coordinator)
            )
            if circuit.current_circuit_flow_temperature is not None:
                sensors.append(
                    lambda: CircuitFlowTemperatureSensor(
                        index, circuit_index, system_coordinator
                    )
                )
            if circuit.heating_curve is not None:
                sensors.append(
                    lambda: CircuitHeatingCurveSensor(
                        index, circuit_index, system_coordinator
                    )
                )
            if circuit.min_flow_temperature_setpoint is not None:
                sensors.append(
                    lambda: CircuitMinFlowTemperatureSetpointSensor(
                        index, circuit_index, system_coordinator
                    )
                )

        for dhw_index, dhw in enumerate(system.domestic_hot_water):
            _LOGGER.debug("Creating Domestic Hot Water sensors for %s", dhw)
            if dhw.current_dhw_temperature:
                sensors.append(
                    lambda: DomesticHotWaterTankTemperatureSensor(
                        index, dhw_index, system_coordinator
                    )
                )
            sensors.append(
                lambda: DomesticHotWaterSetPointSensor(
                    index, dhw_index, system_coordinator
                )
            )
            sensors.append(
                lambda: DomesticHotWaterOperationModeSensor(
                    index, dhw_index, system_coordinator
                )
            )
            sensors.append(
                lambda: DomesticHotWaterCurrentSpecialFunctionSensor(
                    index, dhw_index, system_coordinator
                )
            )
    return sensors


async def create_daily_data_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> EntityList[SensorEntity]:
    daily_data_coordinator: DailyDataCoordinator = hass.data[DOMAIN][config.entry_id][
        "daily_data_coordinator"
    ]

    _LOGGER.debug("Daily data: %s", daily_data_coordinator.data)

    if not daily_data_coordinator.data:
        _LOGGER.warning("No daily data, skipping sensors")
        return EntityList()

    sensors: EntityList[SensorEntity] = EntityList()
    for system_id, system_devices in daily_data_coordinator.data.items():
        _LOGGER.debug("Creating efficiency sensor for System %s", system_id)
        sensors.append(
            lambda: EfficiencySensor(system_id, None, daily_data_coordinator)
        )
        for de_index, devices_data in enumerate(system_devices["devices_data"]):
            if len(devices_data) == 0:
                continue
            _LOGGER.debug(
                "Creating efficiency sensor for System %s and Device %i",
                system_id,
                de_index,
            )
            sensors.append(
                lambda: EfficiencySensor(system_id, de_index, daily_data_coordinator)
            )
            for da_index, _ in enumerate(
                daily_data_coordinator.data[system_id]["devices_data"][de_index]
            ):
                sensors.append(
                    lambda: DataSensor(
                        system_id, de_index, da_index, daily_data_coordinator
                    )
                )

    return sensors


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(await create_system_sensors(hass, config))  # type: ignore
    async_add_entities(await create_daily_data_sensors(hass, config))  # type: ignore


class SystemSensor(SystemCoordinatorEntity, SensorEntity):
    pass


class SystemOutdoorTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self.system.outdoor_temperature is not None:
            return round(self.system.outdoor_temperature, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_outdoor_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} Outdoor Temperature"


class SystemTopDHWTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.cylinder_temperature_sensor_top_dhw is not None:
            return round(self.system.cylinder_temperature_sensor_top_dhw, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_top_dhw_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} Top DHW Cylinder Temperature"


class SystemBottomDHWTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.cylinder_temperature_sensor_bottom_dhw is not None:
            return round(self.system.cylinder_temperature_sensor_bottom_dhw, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_bottom_dhw_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} Bottom DHW Cylinder Temperature"


class SystemTopCHTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.cylinder_temperature_sensor_top_ch is not None:
            return round(self.system.cylinder_temperature_sensor_top_ch, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_top_ch_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} Top Central Heating Cylinder Temperature"


class SystemBottomCHTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.cylinder_temperature_sensor_bottom_ch is not None:
            return round(self.system.cylinder_temperature_sensor_bottom_ch, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_bottom_ch_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} Bottom Central Heating Cylinder Temperature"


class SystemWaterPressureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfPressure.BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.water_pressure is not None:
            return round(self.system.water_pressure, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_water_pressure"

    @property
    def name(self):
        return f"{self.name_prefix} System Water Pressure"


class HomeEntity(CoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(coordinator)
        self.system_index = system_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        rts = {"rts": self.system.rts} if self.system.rts else {}
        mpc = {"mpc": self.system.mpc} if self.system.mpc else {}
        energy_management = (
            {"energy_management": self.system.energy_management}
            if self.system.energy_management
            else {}
        )
        eebus = {"eebus": self.system.eebus} if self.system.eebus else {}
        return (
            self.system.home.extra_fields
            | self.system.extra_fields
            | rts
            | mpc
            | energy_management
            | eebus
        )

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_home"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.system.brand_name,
            model=self.system.home.nomenclature,
            sw_version=self.system.home.firmware_version,
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_base"

    @property
    def native_value(self):
        return self.system.home.firmware_version

    @property
    def name(self):
        return f"{self.system.home.home_name or self.system.home.nomenclature} Firmware Version"


class ZoneDesiredRoomTemperatureSetpointSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.name_prefix} Desired Temperature"

    @property
    def native_value(self):
        return self.zone.desired_room_temperature_setpoint

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_desired_temperature"


class ZoneDesiredRoomTemperatureSetpointHeatingSensor(
    ZoneDesiredRoomTemperatureSetpointSensor
):
    @property
    def name(self):
        return f"{self.name_prefix} Desired Heating Temperature"

    @property
    def native_value(self):
        return self.zone.desired_room_temperature_setpoint_heating

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_desired_heating_temperature"


class ZoneDesiredRoomTemperatureSetpointCoolingSensor(
    ZoneDesiredRoomTemperatureSetpointSensor
):
    @property
    def name(self):
        return f"{self.name_prefix} Desired Cooling Temperature"

    @property
    def native_value(self):
        return self.zone.desired_room_temperature_setpoint_cooling

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_desired_cooling_temperature"


class ZoneCurrentRoomTemperatureSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.name_prefix} Current Temperature"

    @property
    def native_value(self):
        return (
            None
            if self.zone.current_room_temperature is None
            else round(self.zone.current_room_temperature, 1)
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_current_temperature"


class ZoneHumiditySensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.name_prefix} Humidity"

    @property
    def native_value(self):
        return self.zone.current_room_humidity

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_humidity"


class ZoneHeatingOperatingModeSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Heating Operating Mode"

    @property
    def native_value(self):
        return self.zone.heating.operation_mode_heating.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_heating_operating_mode"


class ZoneHeatingStateSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Heating State"

    @property
    def native_value(self):
        if self.zone.heating_state is not None:
            return self.zone.heating_state.display_value
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_heating_state"


class ZoneCurrentSpecialFunctionSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Current Special Function"

    @property
    def native_value(self):
        return self.zone.current_special_function.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_current_special_function"


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
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} Circuit {self.circuit_index}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_circuit_{self.circuit.index}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.id_infix)}}


class CircuitFlowTemperatureSensor(CircuitSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Current Flow Temperature"

    @property
    def native_value(self):
        return self.circuit.current_circuit_flow_temperature

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_flow_temperature"


class CircuitStateSensor(CircuitSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} State"

    @property
    def native_value(self):
        return self.circuit.circuit_state

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return prepare_field_value_for_dict(self.circuit.extra_fields)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_state"


class CircuitMinFlowTemperatureSetpointSensor(CircuitSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Min Flow Temperature Setpoint"

    @property
    def native_value(self):
        return self.circuit.min_flow_temperature_setpoint

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_min_flow_temperature_setpoint"


class CircuitHeatingCurveSensor(CircuitSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Heating Curve"

    @property
    def native_value(self):
        if self.circuit.heating_curve is not None:
            return round(self.circuit.heating_curve, 2)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_heating_curve"


class DomesticHotWaterTankTemperatureSensor(
    DomesticHotWaterCoordinatorEntity, SensorEntity
):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.name_prefix} Tank Temperature"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_dhw_temperature

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_tank_temperature"


class DomesticHotWaterSetPointSensor(DomesticHotWaterCoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return f"{self.name_prefix} Setpoint"

    @property
    def native_value(self) -> float | None:
        return self.domestic_hot_water.tapping_setpoint

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_set_point"


class DomesticHotWaterOperationModeSensor(
    DomesticHotWaterCoordinatorEntity, SensorEntity
):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Operation Mode"

    @property
    def native_value(self):
        return self.domestic_hot_water.operation_mode_dhw.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_operation_mode"


class DomesticHotWaterCurrentSpecialFunctionSensor(
    DomesticHotWaterCoordinatorEntity, SensorEntity
):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Current Special Function"

    @property
    def native_value(self):
        return self.domestic_hot_water.current_special_function.display_value

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_current_special_function"


class DataSensor(CoordinatorEntity, SensorEntity):
    coordinator: DailyDataCoordinator
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        system_id: str,
        de_index: int,
        da_index: int,
        coordinator: DailyDataCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.system_id = system_id
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
    def name(self):
        if self.device_data is None:
            return None
        om = self.device_data.operation_mode.replace("_", " ").title()
        et = (
            self.device_data.energy_type.replace("_", " ").title() + " "
            if self.device_data.energy_type is not None
            else ""
        )
        return f"{self.name_prefix} {et}{om}"

    @property
    def device_data(self) -> DeviceData | None:
        if len(self.coordinator.data[self.system_id]["devices_data"]) <= self.de_index:
            return None
        if (
            len(self.coordinator.data[self.system_id]["devices_data"][self.de_index])
            <= self.da_index
        ):
            return None
        return self.coordinator.data[self.system_id]["devices_data"][self.de_index][
            self.da_index
        ]

    @property
    def home_name(self) -> str:
        return self.coordinator.data[self.system_id]["home_name"]

    @property
    def device(self) -> Device | None:
        if self.device_data is None:
            return None
        return self.device_data.device

    @property
    def total_consumption(self) -> float | None:
        if self.device_data is None:
            return None
        return self.device_data.total_consumption_rounded

    @property
    def unique_id(self) -> str | None:
        if self.device is None:
            return None
        return f"{DOMAIN}_{self.system_id}_{self.device.device_uuid}_{self.da_index}"

    @property
    def name_prefix(self) -> str:
        name_display = f" {self.device.name_display}" if self.device is not None else ""
        return f"{self.home_name} Device {self.de_index}{name_display}"

    @property
    def id_infix(self) -> str:
        return f"{self.system_id}_device_{self.device.device_uuid if self.device is not None else ''}"

    @property
    def device_info(self):
        if self.device is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
            manufacturer=self.device.brand_name,
            model=self.device.product_name_display,
        )

    @property
    def native_value(self):
        return self.device_data.total_consumption_rounded

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


class EfficiencySensor(CoordinatorEntity, SensorEntity):
    coordinator: DailyDataCoordinator
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, system_id: str, de_index: int | None, coordinator: DailyDataCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_id = system_id
        self.de_index = de_index

    @property
    def device_data_list(self) -> list[DeviceData]:
        if self.de_index is None:
            return [
                item
                for row in self.coordinator.data[self.system_id]["devices_data"]
                for item in row
            ]
        else:
            return self.coordinator.data[self.system_id]["devices_data"][self.de_index]

    @property
    def home_name(self) -> str:
        return self.coordinator.data[self.system_id]["home_name"]

    @property
    def energy_consumed(self) -> float:
        """
        Returns total consumed electrical energy for the current day
        """
        return sum(
            [
                v.total_consumption_rounded
                for v in self.device_data_list
                if v.energy_type == "CONSUMED_ELECTRICAL_ENERGY"
            ]
        )

    @property
    def heat_energy_generated(self) -> float:
        """
        Returns total generated heating energy for the current day
        """
        return sum(
            [
                v.total_consumption_rounded
                for v in self.device_data_list
                if v.energy_type == "HEAT_GENERATED"
            ]
        )

    @property
    def unique_id(self) -> str:
        if (
            len(self.device_data_list) > 0
            and self.de_index is not None
            and self.device_data_list[0].device is not None
        ):
            return f"{DOMAIN}_{self.system_id}_device_{self.device_data_list[0].device.device_uuid}_heating_energy_efficiency"
        else:
            return f"{DOMAIN}_{self.system_id}_heating_energy_efficiency"

    @property
    def device_info(self):
        if len(self.device_data_list) == 0:
            return None
        if self.de_index is not None and self.device_data_list[0].device is not None:
            return {
                "identifiers": {
                    (
                        DOMAIN,
                        f"{self.system_id}_device_{self.device_data_list[0].device.device_uuid}",
                    )
                }
            }
        elif self.de_index is None:
            return {"identifiers": {(DOMAIN, f"{self.system_id}_home")}}
        else:
            return None

    @property
    def native_value(self) -> float | None:
        if self.energy_consumed is not None and self.energy_consumed > 0:
            return round(self.heat_energy_generated / self.energy_consumed, 1)
        else:
            return None

    @property
    def name(self):
        if (
            len(self.device_data_list) > 0
            and self.de_index is not None
            and self.device_data_list[0].device is not None
        ):
            return f"{self.home_name} Device {self.de_index} {self.device_data_list[0].device.name_display} Heating Energy Efficiency"
        else:
            return f"{self.home_name} Heating Energy Efficiency"


class SystemDeviceSensor(CoordinatorEntity, SensorEntity):
    coordinator: SystemCoordinator

    def __init__(
        self, system_index: int, device_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(coordinator)
        self.system_index = system_index
        self.device_index = device_index

    @property
    def name_prefix(self) -> str:
        name_display = f" {self.device.name_display}" if self.device is not None else ""
        return f"{self.system.home.home_name or self.system.home.nomenclature} Device {self.device_index}{name_display}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_device_{self.device.device_uuid if self.device is not None else ''}"

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def device(self) -> Device:
        return self.system.devices[self.device_index]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.id_infix)}}


class SystemDeviceWaterPressureSensor(SystemDeviceSensor):
    _attr_native_unit_of_measurement = UnitOfPressure.BAR
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Water Pressure"

    @property
    def native_value(self):
        return self.device.operational_data.get("water_pressure", {}).get("value")

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_water_pressure"


class SystemDeviceOperationTimeSensor(SystemDeviceSensor):
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.device.operation_time is not None:
            return round(self.device.operation_time / 60, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_operation_time"

    @property
    def name(self):
        return f"{self.name_prefix} Operation Time"


class SystemDeviceOnOffCyclesSensor(SystemDeviceSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:counter"

    @property
    def native_value(self):
        if self.device.on_off_cycles is not None:
            return self.device.on_off_cycles
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_on_off_cycles"

    @property
    def name(self):
        return f"{self.name_prefix} On/Off Cycles"


class SystemDeviceCurrentPowerSensor(SystemDeviceSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        if self.device.current_power is not None:
            return self.device.current_power
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_current_power"

    @property
    def name(self):
        return f"{self.name_prefix} Current Power"
