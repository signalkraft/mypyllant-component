from asyncio.exceptions import CancelledError
from aiohttp.client_exceptions import ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    async_get as async_get_device,
    async_entries_for_config_entry,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_registry import (
    async_get as async_get_entity,
    async_entries_for_device,
)


def is_quota_exceeded_exception(exc_info: Exception) -> bool:
    """
    Returns True if the exception is a quota exceeded ClientResponseError
    """
    return (
        isinstance(exc_info, ClientResponseError)
        and exc_info.status == 403
        and "quota exceeded" in exc_info.message.lower()
    )


def is_api_down_exception(exc_info: Exception) -> bool:
    """
    Returns True if the exception indicates that the myVAILLANT API is down
    """
    return isinstance(exc_info, CancelledError) or isinstance(exc_info, TimeoutError)


async def async_remove_orphaned_devices(hass: HomeAssistant, config_entry: ConfigEntry):
    """Remove all devices without entries"""
    entity_registry = async_get_entity(hass)
    device_registry = async_get_device(hass)

    devices = async_entries_for_config_entry(
        hass.data["device_registry"], config_entry.entry_id
    )

    for device in devices:
        if len(async_entries_for_device(entity_registry, device.id)) == 0:
            device_registry.async_remove_device(device.id)
