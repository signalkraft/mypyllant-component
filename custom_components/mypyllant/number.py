from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.mypyllant.const import DOMAIN, DEFAULT_HOLIDAY_SETPOINT
from custom_components.mypyllant.coordinator import SystemCoordinator
from custom_components.mypyllant.utils import (
    HolidayEntity,
    SystemCoordinatorEntity,
    ZoneCoordinatorEntity,
    EntityList,
    CircuitEntity,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping number entities")
        return

    sensors: EntityList[NumberEntity] = EntityList()
    for index, system in enumerate(coordinator.data):
        sensors.append(lambda: SystemHolidayDurationNumber(index, coordinator))
        if system.is_cooling_allowed:
            sensors.append(lambda: SystemManualCoolingDays(index, coordinator))

        for zone_index, zone in enumerate(system.zones):
            sensors.append(
                lambda: ZoneQuickVetoDurationNumber(index, zone_index, coordinator)
            )
        for circuit_index, circuit in enumerate(system.circuits):
            sensors.append(
                lambda: CircuitHeatingCurve(index, circuit_index, coordinator)
            )
            sensors.append(
                lambda: CircuitHeatDemandLimitedByOutsideTemperature(
                    index, circuit_index, coordinator
                )
            )
            sensors.append(
                lambda: CircuitMinFlowTemperatureSetpoint(
                    index, circuit_index, coordinator
                )
            )
    async_add_entities(sensors)  # type: ignore


class SystemHolidayDurationNumber(HolidayEntity, NumberEntity):
    _attr_native_max_value = 365.0
    _attr_icon = "mdi:hvac-off"

    def __init__(self, index: int, coordinator: "SystemCoordinator") -> None:
        super(SystemCoordinatorEntity, self).__init__(coordinator)
        self.index = index

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        if (
            self.holiday_remaining
            and self.holiday_remaining.days > self._attr_native_max_value
        ):
            return self.holiday_remaining.days
        else:
            return self._attr_native_max_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """
        Switch to hours for short durations
        """
        if self.holiday_remaining and self.holiday_remaining.days < 1:
            return UnitOfTime.HOURS
        else:
            return UnitOfTime.DAYS

    @property
    def native_step(self) -> float | None:
        if self.native_unit_of_measurement == UnitOfTime.HOURS:
            return 0.1
        else:
            return super().native_step

    @property
    def name(self):
        return f"{self.name_prefix} Holiday Duration Remaining"

    @property
    def native_value(self):
        if self.holiday_remaining:
            if self.native_unit_of_measurement == UnitOfTime.DAYS:
                return round(self.holiday_remaining.days)
            else:
                return round(self.holiday_remaining.total_seconds() / 3600)
        else:
            return 0

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_holiday(self.system)
            # Holiday values need a long time to show up in the API
            await self.coordinator.async_request_refresh_delayed(20)
        else:
            if self.native_unit_of_measurement == UnitOfTime.DAYS:
                value = value * 24
            end = datetime.now(self.system.timezone) + timedelta(hours=value)
            setpoint = None
            if self.system.control_identifier.is_vrc700:
                setpoint = DEFAULT_HOLIDAY_SETPOINT
            await self.coordinator.api.set_holiday(
                self.system, end=end, setpoint=setpoint
            )
            # Holiday values need a long time to show up in the API
            await self.coordinator.async_request_refresh_delayed(20)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_holiday_duration_remaining"


class SystemManualCoolingDays(SystemCoordinatorEntity, NumberEntity):
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:snowflake"
    _attr_step = 1  # type: ignore

    @property
    def name(self):
        return f"{self.name_prefix} Manual Cooling Duration"

    @property
    def native_value(self):
        return self.system.manual_cooling_days or 0

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_cooling_for_days(self.system)
        else:
            await self.coordinator.api.set_cooling_for_days(
                self.system, duration_days=int(value)
            )
        await self.coordinator.async_request_refresh_delayed(20)

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_manual_cooling_days"

    @property
    def available(self) -> bool:
        return self.system.is_cooling_allowed


class ZoneQuickVetoDurationNumber(ZoneCoordinatorEntity, NumberEntity):
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:rocket-launch"

    @property
    def name(self):
        return f"{self.name_prefix} Quick Veto Duration"

    @property
    def native_value(self):
        return (
            round(self.zone.quick_veto_remaining.total_seconds() / 3600)
            if self.zone.quick_veto_remaining
            else 0
        )

    async def async_set_native_value(self, value: float) -> None:
        if value == 0:
            await self.coordinator.api.cancel_quick_veto_zone_temperature(self.zone)
            await self.coordinator.async_request_refresh_delayed()
        else:
            await self.coordinator.api.quick_veto_zone_duration(self.zone, value)
            await self.coordinator.async_request_refresh_delayed()

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_quick_veto_duration"

    @property
    def available(self) -> bool:
        return self.zone.quick_veto_ongoing


class CircuitHeatingCurve(CircuitEntity, NumberEntity):
    _attr_native_min_value = 0.1
    _attr_native_max_value = 5.0
    _attr_native_step = 0.0000001
    _attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        return self.circuit.heating_curve

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.set_circuit_heating_curve(self.circuit, value)
        await self.coordinator.async_request_refresh_delayed()

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Heating Curve"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN} {self.id_infix}_heating_curve"


class CircuitHeatDemandLimitedByOutsideTemperature(CircuitEntity, NumberEntity):
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:home-thermometer"

    @property
    def native_value(self):
        return self.circuit.heat_demand_limited_by_outside_temperature

    async def async_set_native_value(self, value: float) -> None:
        await (
            self.coordinator.api.set_circuit_heat_demand_limited_by_outside_temperature(
                self.circuit, value
            )
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Heat Demand Limited by Outside Temperature"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN} {self.id_infix}_heat_demand_limited_by_outside_temperature"


class CircuitMinFlowTemperatureSetpoint(CircuitEntity, NumberEntity):
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-water"

    @property
    def native_value(self):
        return self.circuit.heating_flow_temperature_minimum_setpoint

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.set_circuit_min_flow_temperature_setpoint(
            self.circuit, value
        )
        await self.coordinator.async_request_refresh_delayed()

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Min Flow Temperature Setpoint"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN} {self.id_infix}_min_flow_temperature_setpoint"
