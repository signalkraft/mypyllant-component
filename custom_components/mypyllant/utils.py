from asyncio.exceptions import CancelledError

from aiohttp.client_exceptions import ClientResponseError
from myPyllant.models import System


def get_system_sensor_unique_id(system: System) -> str:
    """
    If a primary heat generator exists, we use it as a unique id
    Some sensor names are derived from it, so it made sense at the time to use it for the unique id

    Otherwise, we fall back to the system id
    """
    if system.primary_heat_generator:
        return system.primary_heat_generator.device_uuid
    else:
        return system.id


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
