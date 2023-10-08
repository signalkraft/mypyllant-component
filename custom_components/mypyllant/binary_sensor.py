from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

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
from .utils import get_system_sensor_unique_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping binary sensors")
        return

    sensors: list[BinarySensorEntity] = []
    for index, system in enumerate(coordinator.data):
        sensors.append(ClaimEntity(index, coordinator))
        sensors.append(ControlError(index, coordinator))
        sensors.append(ControlOnline(index, coordinator))
        sensors.append(FirmwareUpdateRequired(index, coordinator))
        for circuit_index, circuit in enumerate(system.circuits):
            sensors.append(CircuitIsCoolingAllowed(index, circuit_index, coordinator))

    async_add_entities(sensors)


class ClaimEntity(CoordinatorEntity, BinarySensorEntity):
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
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "firmware": self.system.claim.firmware,
        }
        return attr

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"claim{self.system.id}")},
            name=self.system.claim.nomenclature,
            manufacturer=self.system.brand_name,
            model=self.system.claim.nomenclature,
            sw_version=self.system.claim.firmware_version,
        )

    @property
    def name(self) -> str:
        return self.system.claim.name


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
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {
                (DOMAIN, f"device{get_system_sensor_unique_id(self.system)}")
            }
        }


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
    def circuit_name(self) -> str:
        return f"Circuit {self.circuit_index}"

    @property
    def circuit(self) -> Circuit:
        return self.coordinator.data[self.system_index].circuits[self.circuit_index]

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            identifiers={(DOMAIN, f"circuit{self.circuit.index}")},
            name=self.circuit_name,
            manufacturer=self.system.brand_name,
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
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        attr = {
            "diagnostic_trouble_codes": self.system.diagnostic_trouble_codes,
        }
        return attr

    @property
    def is_on(self) -> bool | None:
        return self.system.has_diagnostic_trouble_codes

    @property
    def name(self) -> str:
        return f"Trouble Codes on {self.system.system_name}"

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
    def is_on(self) -> bool | None:
        return self.system.connected

    @property
    def name(self) -> str:
        return f"Online Status {self.system.system_name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_control_online_{self.system_index}"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.CONNECTIVITY


class FirmwareUpdateRequired(SystemControlEntity):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, coordinator)
        self.entity_id = f"{DOMAIN}.firmware_update_required_{system_index}"

    @property
    def is_on(self) -> bool | None:
        return self.system.claim.firmware.get("update_required", None)

    @property
    def name(self) -> str:
        return f"Firmware Update Required {self.system.system_name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_firmware_update_required_{self.system_index}"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.UPDATE


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
    def is_on(self) -> bool | None:
        return self.circuit.is_cooling_allowed

    @property
    def name(self) -> str:
        return f"Cooling Allowed in {self.circuit_name}"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_cooling_allowed_{self.circuit_index}"
