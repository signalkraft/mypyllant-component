import functools


def ensure_token_refresh(func):
    """Decorator that adds a check to ensure the session token is refreshed."""

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        await self.coordinator._refresh_session()
        return await func(self, *args, **kwargs)

    return wrapper
