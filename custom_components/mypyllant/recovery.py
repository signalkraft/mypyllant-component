"""Remembers API blocks and setup failures across reloads and restarts."""

from __future__ import annotations

from datetime import datetime as dt, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import API_DOWN_PAUSE_INTERVAL, DOMAIN

STORAGE_VERSION = 1
STORAGE_SAVE_DELAY = 5  # in seconds
SETUP_MAX_BACKOFF = 6 * 3600  # in seconds
SYSTEM_COORDINATOR = "SystemCoordinator"
RECOVERY_INSTANCES = f"{DOMAIN}_recovery"


class SetupRecovery:
    """Per-entry quota blocks and setup backoff, persisted in HA storage"""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.recovery"
        )
        self._data: dict[str, Any] = {
            "blocked_until": {},
            "failures": 0,
            "next_attempt": None,
        }
        self._loaded = False

    @classmethod
    async def async_get(cls, hass: HomeAssistant, entry_id: str) -> SetupRecovery:
        """One instance per entry, so pending writes survive a failed setup"""
        instances = hass.data.setdefault(RECOVERY_INSTANCES, {})
        if entry_id not in instances:
            instances[entry_id] = cls(hass, entry_id)
        recovery = instances[entry_id]
        await recovery._async_load()
        return recovery

    @classmethod
    async def async_remove(cls, hass: HomeAssistant, entry_id: str) -> None:
        recovery = await cls.async_get(hass, entry_id)
        hass.data[RECOVERY_INSTANCES].pop(entry_id)
        await recovery._store.async_remove()

    async def _async_load(self) -> None:
        if self._loaded:
            return
        if stored := await self._store.async_load():
            self._data.update(stored)
        self._loaded = True

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(lambda: self._data, STORAGE_SAVE_DELAY)

    @staticmethod
    def _future(value: str | None) -> dt | None:
        if not value:
            return None
        parsed = dt.fromisoformat(value)
        return parsed if parsed > dt.now(timezone.utc) else None

    @callback
    def blocked_until(self, name: str) -> dt | None:
        return self._future(self._data["blocked_until"].get(name))

    @callback
    def set_blocked(self, name: str, until: dt) -> None:
        self._data["blocked_until"][name] = until.isoformat()
        self._save()

    @callback
    def clear_blocked(self, name: str) -> None:
        if self._data["blocked_until"].pop(name, None) is not None:
            self._save()

    @callback
    def next_setup_attempt(self) -> dt | None:
        """When setup may call the API again, None if it may do so now"""
        times = [
            t
            for t in (
                self.blocked_until(SYSTEM_COORDINATOR),
                self._future(self._data["next_attempt"]),
            )
            if t
        ]
        return max(times) if times else None

    @callback
    def record_setup_failure(self) -> int:
        """Doubles the pause on every consecutive failure, returns it in seconds"""
        self._data["failures"] += 1
        delay = min(
            API_DOWN_PAUSE_INTERVAL * 2 ** (self._data["failures"] - 1),
            SETUP_MAX_BACKOFF,
        )
        self._data["next_attempt"] = (
            dt.now(timezone.utc) + timedelta(seconds=delay)
        ).isoformat()
        self._save()
        return delay

    @callback
    def record_setup_success(self) -> None:
        if self._data["failures"] or self._data["next_attempt"]:
            self._data["failures"] = 0
            self._data["next_attempt"] = None
            self._save()
