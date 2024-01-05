from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from custom_components.mypyllant.entities.circuit import (
    CircuitFlowTemperatureSensor,
    CircuitHeatingCurveSensor,
    CircuitMinFlowTemperatureSetpointSensor,
    CircuitStateSensor,
)
from custom_components.mypyllant.entities.device import (
    DataSensor,
    DeviceEfficiencySensor,
    SystemDeviceWaterPressureSensor,
)
from custom_components.mypyllant.entities.dhw import (
    DomesticHotWaterCurrentSpecialFunctionSensor,
    DomesticHotWaterOperationModeSensor,
    DomesticHotWaterSetPointSensor,
    DomesticHotWaterTankTemperatureSensor,
)
from custom_components.mypyllant.entities.system import (
    HomeEntity,
    SystemEfficiencySensor,
    SystemOutdoorTemperatureSensor,
    SystemWaterPressureSensor,
)
from custom_components.mypyllant.entities.zone import (
    ZoneCurrentRoomTemperatureSensor,
    ZoneCurrentSpecialFunctionSensor,
    ZoneDesiredRoomTemperatureSetpointSensor,
    ZoneHeatingOperatingModeSensor,
    ZoneHeatingStateSensor,
    ZoneHumiditySensor,
)


from . import DailyDataCoordinator, SystemCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
    _LOGGER.debug("Creating system sensors for %s", system_coordinator.data)
    for index, system in enumerate(system_coordinator.data):
        if system.outdoor_temperature is not None:
            sensors.append(SystemOutdoorTemperatureSensor(index, system_coordinator))
        if system.water_pressure is not None:
            sensors.append(SystemWaterPressureSensor(index, system_coordinator))
        sensors.append(HomeEntity(index, system_coordinator))

        for device_index, device in enumerate(system.devices):
            _LOGGER.debug("Creating SystemDevice sensors for %s", device)

            if "water_pressure" in device.operational_data:
                sensors.append(
                    SystemDeviceWaterPressureSensor(
                        index, device_index, system_coordinator
                    )
                )

        for zone_index, zone in enumerate(system.zones):
            _LOGGER.debug("Creating Zone sensors for %s", zone)
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
            _LOGGER.debug("Creating Circuit sensors for %s", circuit)
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
            _LOGGER.debug("Creating Domestic Hot Water sensors for %s", dhw)
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

    _LOGGER.debug("Daily data: %s", daily_data_coordinator.data)

    if not daily_data_coordinator.data:
        _LOGGER.warning("No daily data, skipping sensors")
        return []

    sensors: list[SensorEntity] = []
    for system_index, system_devices in enumerate(daily_data_coordinator.data):
        _LOGGER.debug("Creating efficiency sensor for System %s", system_index)
        sensors.append(SystemEfficiencySensor(system_index, daily_data_coordinator))
        for de_index, devices_data in enumerate(system_devices["devices_data"]):
            if len(devices_data) == 0:
                continue
            _LOGGER.debug(
                "Creating efficiency sensor for System %s and Device %i",
                system_index,
                de_index,
            )
            sensors.append(
                DeviceEfficiencySensor(system_index, de_index, daily_data_coordinator)
            )
            for da_index, _ in enumerate(
                daily_data_coordinator.data[system_index]["devices_data"][de_index]
            ):
                sensors.append(
                    DataSensor(system_index, de_index, da_index, daily_data_coordinator)
                )

    return sensors


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(await create_system_sensors(hass, config))
    async_add_entities(await create_daily_data_sensors(hass, config))
