from asyncio.exceptions import CancelledError

from aiohttp.client_exceptions import ClientResponseError
from custom_components.mypyllant.const import DOMAIN


def get_unique_id_prefix(system_id: str) -> str:
    return f"{DOMAIN}_{system_id}_"


def get_name_prefix(home: str) -> str:
    return f"{home} "


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
