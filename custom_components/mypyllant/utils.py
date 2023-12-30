from asyncio.exceptions import CancelledError

from aiohttp.client_exceptions import ClientResponseError


def shorten_zone_name(zone_name: str) -> str:
    if zone_name.startswith("Zone "):
        return zone_name[5:]
    return zone_name


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
