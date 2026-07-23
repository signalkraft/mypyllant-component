from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
    async_add_external_statistics,
    statistics_during_period,
)
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
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
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


async def create_system_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> EntityList[SensorEntity]:
    system_coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not system_coordinator.data:
        _LOGGER.debug("No system data, skipping sensors")
        return EntityList()

    sensors: EntityList[SensorEntity] = EntityList()
    _LOGGER.debug("Creating system sensors for %s", system_coordinator.data)
    sensors.append(lambda: SystemAPIRequestCount(system_coordinator))
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
        if system.system_flow_temperature is not None:
            sensors.append(
                lambda: SystemFlowTemperatureSensor(index, system_coordinator)
            )
        if system.energy_manager_state is not None:
            sensors.append(
                lambda: SystemEnergyManagerStateSensor(index, system_coordinator)
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
            if zone.cooling is not None:
                sensors.append(
                    lambda: ZoneCoolingOperatingModeSensor(
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
            if circuit.heating_circuit_flow_setpoint is not None:
                sensors.append(
                    lambda: CircuitFlowTemperatureSetpointSensor(
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


def create_scf_sensors(
    hass: HomeAssistant, config: ConfigEntry
) -> EntityList[SensorEntity]:
    """Sensors for scf/iQconnect systems (separate data path, see coordinator.scf_systems)."""
    from custom_components.mypyllant.scf_entity import ScfSensor

    system_coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    sensors: EntityList[SensorEntity] = EntityList()
    for system in getattr(system_coordinator, "scf_systems", []):
        for point in system.by_platform("sensor"):
            sensors.append(lambda p=point: ScfSensor(system_coordinator, p))
    return sensors


def register_scf_schedule_service(hass: HomeAssistant, config: ConfigEntry) -> None:
    """Register the mypyllant.scf_set_schedule entity service on the sensor platform.

    Only when scf systems exist. The set_schedule handler lives on ScfSensor; HA resolves
    the target (the schedule sensor) to the entity itself."""
    import voluptuous as vol
    from homeassistant.helpers import entity_platform

    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not getattr(coordinator, "scf_systems", []):
        return
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "scf_set_schedule",
        {vol.Required("schedule"): dict},
        "set_schedule",
    )


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = await create_system_sensors(hass, config)
    entities.extend(create_scf_sensors(hass, config))
    async_add_entities(entities)  # type: ignore
    async_add_entities(await create_daily_data_sensors(hass, config))  # type: ignore
    register_scf_schedule_service(hass, config)


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
    coordinator: SystemCoordinator

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


class ZoneCoolingOperatingModeSensor(ZoneCoordinatorEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Cooling Operating Mode"

    @property
    def native_value(self):
        if self.zone.cooling is not None:
            return self.zone.cooling.operation_mode_cooling.display_value
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_cooling_operating_mode"


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


class CircuitFlowTemperatureSetpointSensor(CircuitSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self):
        return f"{self.name_prefix} Flow Temperature Setpoint"

    @property
    def native_value(self):
        return self.circuit.heating_circuit_flow_setpoint

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_flow_temperature_setpoint"


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
        # heating_circuit_flow_setpoint was previously surfaced via extra_fields
        # but was promoted to a typed Circuit field upstream (see #422, #440).
        # Merge it back in explicitly so existing automations/templates reading
        # state_attr('sensor.<>_circuit_0_state', 'heating_circuit_flow_setpoint')
        # keep working. prepare_field_value_for_dict must still run on
        # extra_fields because it contains a zoneinfo.ZoneInfo value that is
        # not JSON-serialisable raw.
        return prepare_field_value_for_dict(self.circuit.extra_fields) | {
            "heating_circuit_flow_setpoint": self.circuit.heating_circuit_flow_setpoint,
        }

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
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._unsub_midnight: CALLBACK_TYPE | None = None
        _LOGGER.debug(
            "Finishing init of %s = %s and unique id %s",
            self.name,
            self.native_value,
            self.unique_id,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.data:
            await self._safe_write_hourly_statistics()
        self._unsub_midnight = async_track_time_change(
            self.hass, self._handle_midnight, hour=0, minute=0, second=1
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_midnight:
            self._unsub_midnight()

    @callback
    def _handle_midnight(self, now: datetime) -> None:
        self.async_write_ha_state()

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
    def today_total_consumption(self) -> float:
        # The coordinator fetches a 2-day window (yesterday + today) so
        # _write_hourly_statistics can backfill yesterday's last hour after
        # midnight (see coordinator.py). device_data.total_consumption is the
        # API's own aggregate for that whole 2-day range, so it can't be used
        # here - it would never reset to 0 at midnight. Sum only today's own
        # buckets instead, using the same bucket-midnight comparison
        # _write_hourly_statistics already uses, so the two stay consistent.
        #
        # "Today" is anchored to the actual current time in the device's own
        # timezone, not to the last fetched bucket's date: right after
        # midnight the API can briefly lag behind and not yet have a bucket
        # for the new day, so data[-1] would still be yesterday, causing this
        # to sum yesterday's total again instead of resetting to 0.
        if self.device_data is None or not self.device_data.data:
            return 0.0
        tzinfo = self.device_data.data[-1].start_date.tzinfo
        today = datetime.now(tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
        total = sum(
            bucket.value
            for bucket in self.device_data.data
            if bucket.value is not None
            and bucket.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            == today
        )
        return round(total / 1000, 1) * 1000 if total else 0.0

    @property
    def unique_id(self) -> str | None:
        if self.device is None:
            return None
        return f"{DOMAIN}_{self.system_id}_{self.device.device_uuid}_{self.da_index}_{self.de_index}"

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
        if self.device_data:
            return self.today_total_consumption
        else:
            return None

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
        self.hass.async_create_task(self._safe_write_hourly_statistics())

    async def _safe_write_hourly_statistics(self) -> None:
        try:
            await self._write_hourly_statistics()
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to write hourly statistics for %s; will retry on next update",
                self.unique_id,
                exc_info=True,
            )

    async def _write_hourly_statistics(self) -> None:
        if (
            self.unique_id is None
            or self.device_data is None
            or not self.device_data.data
        ):
            return
        statistic_id = f"{DOMAIN}:{self.unique_id}".lower().replace("-", "_")

        window_start = self.device_data.data[0].start_date
        window_end = self.device_data.data[-1].start_date + timedelta(hours=1)

        # Baseline is the last-published sum strictly BEFORE this window, never the
        # single most-recent stat ever recorded. get_last_statistics(1, ...) is
        # unbounded - once any later window has been written, it returns a value
        # that already includes this window's own buckets, so recomputing
        # baseline + sum(this window's buckets) double-counts them and the sum
        # grows on every single poll forever. Bounding the lookup to end at
        # window_start keeps the baseline stable across repeated polls of the
        # same window, so the existing-buckets dedup guard below can actually
        # recognize unchanged buckets instead of rewriting everything every time.
        last_stats = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            window_start - timedelta(days=7),
            window_start,
            {statistic_id},
            "hour",
            None,
            {"sum"},
        )
        baseline_sum = (
            last_stats[statistic_id][-1]["sum"] or 0.0
            if statistic_id in last_stats and last_stats[statistic_id]
            else 0.0
        )

        # Buckets already published for this window, keyed by start timestamp, so we
        # only (re)write buckets that are new or whose value actually changed (a
        # late API correction) - not every bucket on every run. Rewriting the whole
        # window unconditionally re-anchors already-published, stable history to
        # whatever baseline happens to be current, which breaks the daily reset.
        existing_stats = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            window_start,
            window_end,
            {statistic_id},
            "hour",
            None,
            {"sum"},
        )
        existing_sums = {
            row["start"]: row["sum"]
            for row in existing_stats.get(statistic_id, [])
            if "start" in row
        }

        # The coordinator fetches a 2-day window (yesterday + today) so the previous
        # day's final hour can still be backfilled once it finalises after midnight.
        # sum stays monotonic (cumulative since baseline), while state and last_reset
        # reset to the start of each day, mirroring octopus_energy's day-cumulative
        # state.
        running_sum = baseline_sum
        running_state = 0.0
        current_day = None
        stats: list[StatisticData] = []
        for bucket in self.device_data.data:
            if bucket.value is None:
                continue
            bucket_midnight = bucket.start_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            if current_day != bucket_midnight:
                running_state = 0.0
                current_day = bucket_midnight
            running_sum += bucket.value
            running_state += bucket.value
            existing_sum = existing_sums.get(bucket.start_date.timestamp())
            if existing_sum is not None and existing_sum == running_sum:
                continue
            stats.append(
                StatisticData(
                    start=bucket.start_date,
                    last_reset=bucket_midnight,
                    sum=running_sum,
                    state=running_state,
                )
            )
        if not stats:
            return
        async_add_external_statistics(
            self.hass,
            StatisticMetaData(
                mean_type=StatisticMeanType.NONE,
                has_sum=True,
                name=self.name,
                source=DOMAIN,
                statistic_id=statistic_id,
                unit_class="energy",
                unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            ),
            stats,
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
    _attr_device_class = SensorDeviceClass.POWER

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


class SystemAPIRequestCount(SensorEntity, CoordinatorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return self.coordinator.api.aiohttp_session.request_count

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_api_request_count"

    @property
    def name(self):
        return "Vaillant API Request Count"


class SystemFlowTemperatureSensor(SystemSensor):
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.system.system_flow_temperature is not None:
            return round(self.system.system_flow_temperature, 1)
        else:
            return None

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_system_flow_temperature"

    @property
    def name(self):
        return f"{self.name_prefix} System Flow Temperature"


class SystemEnergyManagerStateSensor(SystemSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.system.energy_manager_state

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_energy_manager_state"

    @property
    def name(self):
        return f"{self.name_prefix} Energy Manager State"
