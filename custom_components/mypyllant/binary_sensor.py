from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from myPyllant.models import Circuit, System

from . import SystemCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]

    sensors: list[BinarySensorEntity] = []
    for index, system in enumerate(coordinator.data):
        sensors.append(ControlError(index, coordinator))
        sensors.append(ControlOnline(index, coordinator))
        for circuit_index, circuit in enumerate(system.circuits):
            sensors.append(CircuitIsCoolingAllowed(index, circuit_index, coordinator))

    async_add_entities(sensors)


class SystemControlEntity(CoordinatorEntity, BinarySensorEntity):
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
    def control(self):
        devices = [d for d in self.system.devices if d["type"] == "CONTROL"]
        if len(devices) > 0:
            return devices[0]
        return None

    @property
    def name(self) -> System:
        return self.control["name"] if self.control else None

    @property
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo | None:
        if self.control:
            return DeviceInfo(
                identifiers={(DOMAIN, f"system{self.system.id}")},
                name=self.control["name"],
                manufacturer="Vaillant",
                model=self.control["name"],
            )
        return None


class CircuitEntity(CoordinatorEntity, BinarySensorEntity):
    def __init__(
        self,
        system_index: int,
        circuit_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(coordinator)
        self.system_index = system_index
        self.circuit_index = circuit_index

    @property
    def system(self) -> System:
        return self.coordinator.data[self.system_index]

    @property
    def name(self) -> str:
        return f"Circuit {self.circuit_index}"

    @property
    def circuit(self) -> Circuit:
        return self.coordinator.data[self.system_index].circuits[self.circuit_index]

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            identifiers={(DOMAIN, f"circuit{self.circuit.index}")},
            name=f"Circuit {self.circuit.index}",
            manufacturer="Vaillant",
        )


class ControlError(SystemControlEntity):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, coordinator)
        self.entity_id = f"{DOMAIN}.control_error_{system_index}"

    @property
    def is_on(self) -> bool:
        return self.system.status_error

    @property
    def name(self) -> str:
        return f"Error {super().name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_control_error_{self.system_index}"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.PROBLEM


class ControlOnline(SystemControlEntity):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, coordinator)
        self.entity_id = f"{DOMAIN}.control_online_{system_index}"

    @property
    def is_on(self) -> bool:
        return self.system.status_online

    @property
    def name(self) -> str:
        return f"Online Status {super().name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_control_online_{self.system_index}"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.CONNECTIVITY


class CircuitIsCoolingAllowed(CircuitEntity):
    def __init__(
        self,
        system_index: int,
        circuit_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, circuit_index, coordinator)
        self.entity_id = f"{DOMAIN}.circuit_is_cooling_allowed_{system_index}"

    @property
    def is_on(self) -> bool:
        return self.circuit.is_cooling_allowed

    @property
    def name(self) -> str:
        return f"Cooling Allowed in {super().name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_cooling_allowed_{self.circuit_index}"
