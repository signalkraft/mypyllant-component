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
from .utils import get_name_prefix, get_system_sensor_unique_id, get_unique_id_prefix

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
        sensors.append(ControlError(index, coordinator))
        sensors.append(ControlOnline(index, coordinator))
        sensors.append(FirmwareUpdateRequired(index, coordinator))
        sensors.append(FirmwareUpdateEnabled(index, coordinator))
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
    def entity_category(self) -> EntityCategory | None:
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {
                (DOMAIN, f"device_{get_system_sensor_unique_id(self.system)}")
            }
        }


class ControlError(SystemControlEntity):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, coordinator)

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
        return f"{get_name_prefix(self.system.home.name)}Trouble Codes on {self.system.system_name}"

    @property
    def unique_id(self) -> str:
        return f"{get_unique_id_prefix(self.system.id)}control_error"

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

    @property
    def is_on(self) -> bool:
        return self.system.connected is True

    @property
    def name(self) -> str:
        return f"{get_name_prefix(self.system.home.name)}Online Status"

    @property
    def unique_id(self) -> str:
        return f"{get_unique_id_prefix(self.system.id)}control_online"

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

    @property
    def is_on(self) -> bool | None:
        return self.system.home.firmware.get("update_required", None)

    @property
    def name(self) -> str:
        return f"{get_name_prefix(self.system.home.name)}Firmware Update Required"

    @property
    def unique_id(self) -> str:
        return f"{get_unique_id_prefix(self.system.id)}firmware_update_required"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.UPDATE

    @property
    def device_info(self) -> DeviceInfo | None:
        return {"identifiers": {(DOMAIN, f"home_{self.system.id}")}}


class FirmwareUpdateEnabled(SystemControlEntity):
    def __init__(
        self,
        system_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, coordinator)

    @property
    def is_on(self) -> bool | None:
        return self.system.home.firmware.get("update_enabled", None)

    @property
    def name(self) -> str:
        return f"{get_name_prefix(self.system.home.name)}Firmware Update Enabled"

    @property
    def unique_id(self) -> str:
        return f"{get_unique_id_prefix(self.system.id)}firmware_update_enabled"

    @property
    def device_info(self) -> DeviceInfo | None:
        return {"identifiers": {(DOMAIN, f"home_{self.system.id}")}}


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
    def circuit(self) -> Circuit:
        return self.coordinator.data[self.system_index].circuits[self.circuit_index]

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            identifiers={(DOMAIN, f"circuit_{self.system.id}_{self.circuit.index}")},
            name=f"{get_name_prefix(self.system.home.name)}Circuit {self.circuit_index}",
            manufacturer=self.system.brand_name,
        )


class CircuitIsCoolingAllowed(CircuitEntity):
    def __init__(
        self,
        system_index: int,
        circuit_index: int,
        coordinator: SystemCoordinator,
    ):
        super().__init__(system_index, circuit_index, coordinator)

    @property
    def is_on(self) -> bool | None:
        return self.circuit.is_cooling_allowed

    @property
    def name(self) -> str:
        return f"{get_name_prefix(self.system.home.name)}Cooling Allowed in {self.circuit_index}"

    @property
    def unique_id(self) -> str:
        return f"{get_unique_id_prefix(self.system.id)}cooling_allowed_{self.circuit_index}"
