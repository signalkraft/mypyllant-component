import functools

def ensure_token_refresh(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        await self.coordinator._refresh_session()
        return await func(self, *args, **kwargs)
    return wrapper
