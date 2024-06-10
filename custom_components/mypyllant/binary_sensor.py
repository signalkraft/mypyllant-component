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
from .utils import (
    EntityList,
    AmbisenseDeviceCoordinatorEntity,
    AmbisenseCoordinatorEntity,
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
        _LOGGER.warning("No system data, skipping binary sensors")
        return

    sensors: EntityList[BinarySensorEntity] = EntityList()
    for index, system in enumerate(coordinator.data):
        sensors.append(lambda: ControlError(index, coordinator))
        sensors.append(lambda: ControlOnline(index, coordinator))
        sensors.append(lambda: FirmwareUpdateRequired(index, coordinator))
        sensors.append(lambda: FirmwareUpdateEnabled(index, coordinator))
        for circuit_index, circuit in enumerate(system.circuits):
            sensors.append(
                lambda: CircuitIsCoolingAllowed(index, circuit_index, coordinator)
            )

        for room in system.ambisense_rooms:
            _LOGGER.debug("Creating room binary sensors for %s", room)
            sensors.append(
                lambda: AmbisenseWindowStateEntity(index, room.room_index, coordinator)
            )
            sensors.append(
                lambda: AmbisenseButtonLockEntity(index, room.room_index, coordinator)
            )
            for device in room.room_configuration.devices:
                _LOGGER.debug("Creating room device binary sensors for %s", device)
                sensors.append(
                    lambda: AmbisenseLowBatteryEntity(
                        index, room.room_index, device.sgtin, coordinator
                    )
                )

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
    def id_infix(self) -> str:
        return f"{self.system.id}_home"

    @property
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature}"

    @property
    def device_info(self) -> DeviceInfo | None:
        return {"identifiers": {(DOMAIN, self.id_infix)}}


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
        return f"{self.name_prefix} Trouble Codes"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_control_error"

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
        return f"{self.name_prefix} Online Status"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_control_online"

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
        return f"{self.name_prefix} Firmware Update Required"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_firmware_update_required"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.UPDATE


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
        return f"{self.name_prefix} Firmware Update Enabled"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_firmware_update_enabled"


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
    def name_prefix(self) -> str:
        return f"{self.system.home.home_name or self.system.home.nomenclature} Circuit {self.circuit_index}"

    @property
    def id_infix(self) -> str:
        return f"{self.system.id}_circuit_{self.circuit.index}"

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(
            identifiers={(DOMAIN, self.id_infix)},
            name=self.name_prefix,
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
        return f"{self.name_prefix} Cooling Allowed"

    @property
    def unique_id(self) -> str:
        # TODO: Add migration to remove space from ID
        return f"{DOMAIN} {self.id_infix}_cooling_allowed"


class AmbisenseWindowStateEntity(AmbisenseCoordinatorEntity, BinarySensorEntity):
    @property
    def icon(self) -> str | None:
        if self.is_on:
            return "mdi:window-open-variant"
        else:
            return "mdi:window-closed-variant"

    @property
    def is_on(self) -> bool | None:
        return self.room.room_configuration.window_state

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Window State"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_window_state"


class AmbisenseButtonLockEntity(AmbisenseCoordinatorEntity, BinarySensorEntity):
    @property
    def icon(self) -> str | None:
        if self.is_on:
            return "mdi:lock"
        else:
            return "mdi:lock-open"

    @property
    def is_on(self) -> bool | None:
        return self.room.room_configuration.button_lock

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Button Lock"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_button_lock"


class AmbisenseLowBatteryEntity(AmbisenseDeviceCoordinatorEntity, BinarySensorEntity):
    @property
    def icon(self) -> str | None:
        if self.is_on:
            return "mdi:battery-alert"
        else:
            return "mdi:battery-check"

    @property
    def is_on(self) -> bool | None:
        return self.device.low_bat

    @property
    def name(self) -> str:
        return f"{self.name_prefix} Low Battery"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.id_infix}_low_battery"
