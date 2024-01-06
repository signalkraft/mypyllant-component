from abc import ABC
from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant.entities.base import (
    BaseSystemCoordinatorEntity,
    BaseTemperatureEntity,
)

from myPyllant.models import Circuit, Zone
from homeassistant.helpers.entity import EntityCategory

from homeassistant.components.sensor import SensorStateClass, SensorEntity

from homeassistant.components.binary_sensor import BinarySensorEntity

from collections.abc import Mapping
from typing import Any

from custom_components.mypyllant.entities.zone import zone_device_name
from myPyllant.utils import prepare_field_value_for_dict


class BaseCircuit(BaseSystemCoordinatorEntity, ABC):
    def __init__(
        self, system_index: int, circuit_index: int, coordinator: SystemCoordinator
    ) -> None:
        super().__init__(system_index, coordinator)
        self.circuit_index = circuit_index

    @property
    def name_prefix(self) -> str:
        # merge circuit into zone if it is unambiguously
        if self.zone is not None:
            return f"{super().name_prefix} {zone_device_name(self.system, self.zone)}"
        return f"{super().name_prefix} Circuit {self.circuit_index}"

    @property
    def id_infix(self) -> str:
        return f"{super().id_infix}_circuit_{self.circuit.index}"

    @property
    def circuit(self) -> Circuit:
        return self.system.circuits[self.circuit_index]

    @property
    def zone(self) -> Zone | None:
        res = [
            x
            for x in self.system.zones
            if x.associated_circuit_index == self.circuit_index
        ]
        if len(res) == 1:
            return res[0]
        return None

    @property
    def device_info(self):
        device = super().device_info

        # merge circuit into zone if it is unambiguously
        if self.zone is not None:
            device.update(
                identifiers={(DOMAIN, f"{self.system.id}_zone_{self.zone.index}")}
            )

        return device


class CircuitFlowTemperatureSensor(BaseCircuit, BaseTemperatureEntity):
    @property
    def name_suffix(self):
        return "Current Flow Temperature"

    @property
    def id_suffix(self) -> str:
        return "flow_temperature"

    @property
    def native_value(self):
        return self.circuit.current_circuit_flow_temperature

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class CircuitStateSensor(BaseCircuit, SensorEntity):
    @property
    def name_suffix(self):
        return "State"

    @property
    def id_suffix(self) -> str:
        return "state"

    @property
    def native_value(self):
        return self.circuit.circuit_state

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return prepare_field_value_for_dict(self.circuit.extra_fields)


class CircuitMinFlowTemperatureSetpointSensor(BaseCircuit, BaseTemperatureEntity):
    @property
    def name_suffix(self):
        return "Min Flow Temperature Setpoint"

    @property
    def id_suffix(self) -> str:
        return "min_flow_temperature_setpoint"

    @property
    def native_value(self):
        return self.circuit.min_flow_temperature_setpoint

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class CircuitHeatingCurveSensor(BaseCircuit, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name_suffix(self):
        return "Heating Curve"

    @property
    def id_suffix(self) -> str:
        return "heating_curve"

    @property
    def native_value(self):
        if self.circuit.heating_curve is not None:
            return round(self.circuit.heating_curve, 2)
        else:
            return None

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC


class CircuitIsCoolingAllowed(BaseCircuit, BinarySensorEntity):
    @property
    def name_suffix(self) -> str:
        return "Cooling Allowed"

    @property
    def id_suffix(self) -> str:
        return "cooling_allowed"

    @property
    def is_on(self) -> bool | None:
        return self.circuit.is_cooling_allowed
