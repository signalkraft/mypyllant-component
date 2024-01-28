from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform, selector
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import as_datetime
from myPyllant.const import (
    MANUAL_SETPOINT_TYPES,
)
from myPyllant.models import (
    VentilationFanStageType,
)

from custom_components.mypyllant.entities.ventilation import VentilationClimate
from custom_components.mypyllant.entities.zone import ZoneClimate


from . import SystemCoordinator
from .const import (
    DOMAIN,
    SERVICE_CANCEL_HOLIDAY,
    SERVICE_CANCEL_QUICK_VETO,
    SERVICE_SET_HOLIDAY,
    SERVICE_SET_MANUAL_MODE_SETPOINT,
    SERVICE_SET_QUICK_VETO,
    SERVICE_SET_VENTILATION_FAN_STAGE,
    SERVICE_SET_ZONE_TIME_PROGRAM,
)

_LOGGER = logging.getLogger(__name__)

_MANUAL_SETPOINT_TYPES_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v)
    for k, v in MANUAL_SETPOINT_TYPES.items()
]

_FAN_STAGE_TYPE_OPTIONS = [
    selector.SelectOptionDict(value=v.value, label=v.value.title())
    for v in VentilationFanStageType
]


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    coordinator: SystemCoordinator = hass.data[DOMAIN][config.entry_id][
        "system_coordinator"
    ]
    if not coordinator.data:
        _LOGGER.warning("No system data, skipping climate")
        return

    zone_entities: list[ClimateEntity] = []
    ventilation_entities: list[ClimateEntity] = []

    for index, system in enumerate(coordinator.data):
        for zone_index, _ in enumerate(system.zones):
            zone_entities.append(
                ZoneClimate(
                    index,
                    zone_index,
                    coordinator,
                    config,
                )
            )
        for ventilation_index, _ in enumerate(system.ventilation):
            ventilation_entities.append(
                VentilationClimate(
                    index,
                    ventilation_index,
                    coordinator,
                )
            )

    async_add_entities(zone_entities)
    async_add_entities(ventilation_entities)

    if len(zone_entities) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up zone climate entity services for %s", platform)
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_QUICK_VETO,
            {
                vol.Required("temperature"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=0, max=30)
                ),
                vol.Optional("duration_hours"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=1)
                ),
            },
            "set_quick_veto",
        )
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_MANUAL_MODE_SETPOINT,
            {
                vol.Required("temperature"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=0, max=30)
                ),
                vol.Required("setpoint_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_MANUAL_SETPOINT_TYPES_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
            },
            "set_manual_mode_setpoint",
        )
        platform.async_register_entity_service(
            SERVICE_CANCEL_QUICK_VETO,
            {},
            "remove_quick_veto",
        )
        # noinspection PyTypeChecker
        platform.async_register_entity_service(
            SERVICE_SET_HOLIDAY,
            {
                vol.Optional("start"): vol.Coerce(as_datetime),
                vol.Optional("end"): vol.Coerce(as_datetime),
                vol.Optional("duration_hours"): vol.All(
                    vol.Coerce(float), vol.Clamp(min=1)
                ),
            },
            "set_holiday",
        )
        platform.async_register_entity_service(
            SERVICE_CANCEL_HOLIDAY,
            {},
            "cancel_holiday",
        )
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_ZONE_TIME_PROGRAM,
            {
                vol.Required("program_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value="heating", label="Heating"),
                            selector.SelectOptionDict(value="cooling", label="Cooling"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("time_program"): vol.All(dict),
            },
            "set_zone_time_program",
        )

    if len(ventilation_entities) > 0:
        platform = entity_platform.async_get_current_platform()
        _LOGGER.debug("Setting up ventilation climate entity services for %s", platform)
        # noinspection PyTypeChecker
        # Wrapping the schema in vol.Schema() breaks entity_id passing
        platform.async_register_entity_service(
            SERVICE_SET_VENTILATION_FAN_STAGE,
            {
                vol.Required("maximum_fan_stage"): vol.All(
                    vol.Coerce(int), vol.Clamp(min=1, max=6)
                ),
                vol.Required("fan_stage_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_FAN_STAGE_TYPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    ),
                ),
            },
            "set_ventilation_fan_stage",
        )
