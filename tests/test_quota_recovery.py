from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from aiohttp import RequestInfo
from aiohttp.client_exceptions import ClientResponseError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from myPyllant.api import AmbisenseNoFacilityError
from myPyllant.http_client import AuthenticationFailed, LoginEndpointInvalid

from custom_components.mypyllant import async_setup_entry
from custom_components.mypyllant.const import (
    API_DOWN_PAUSE_INTERVAL,
    DOMAIN,
)
from custom_components.mypyllant.recovery import (
    RECOVERY_INSTANCES,
    SETUP_MAX_BACKOFF,
    SYSTEM_COORDINATOR,
    SetupRecovery,
)
from custom_components.mypyllant.coordinator import (
    DailyDataCoordinator,
    SystemCoordinator,
)
from custom_components.mypyllant.sensor import (
    DAILY_SENSORS_RETRY_INTERVAL,
    async_add_daily_sensors_when_ready,
)
from custom_components.mypyllant.utils import extract_quota_duration


def quota_error(duration: str) -> ClientResponseError:
    return ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/",  # type: ignore
            method="GET",
            headers=None,  # type: ignore
        ),
        history=None,  # type: ignore
        status=403,
        message=f"Out of call volume quota. Quota will be replenished in {duration}.",
    )


@pytest.mark.parametrize(
    "duration,seconds",
    [
        ("00:44:32", 2672),
        ("04:16:47", 15407),
        ("1.02:02:00", 93720),
        ("5.12:32:57", 477177),
        ("12.00:00:01", 1036801),
    ],
)
def test_extract_quota_duration_with_days(duration, seconds):
    assert extract_quota_duration(quota_error(duration)) == seconds


@pytest.fixture
def daily_setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {entry.entry_id: {}}
    coordinator = DailyDataCoordinator(hass, mock.Mock(), entry, None)
    hass.data[DOMAIN][entry.entry_id]["daily_data_coordinator"] = coordinator
    return entry, coordinator


async def test_daily_sensors_added_after_recovery(hass, daily_setup):
    entry, coordinator = daily_setup
    add_entities = mock.Mock()
    async_add_daily_sensors_when_ready(hass, entry, coordinator, add_entities)
    assert coordinator.update_interval == DAILY_SENSORS_RETRY_INTERVAL

    coordinator.last_update_success = False
    coordinator.async_update_listeners()
    await hass.async_block_till_done()
    add_entities.assert_not_called()

    with mock.patch(
        "custom_components.mypyllant.sensor.create_daily_data_sensors",
        new=mock.AsyncMock(return_value=["sensor"]),
    ):
        coordinator.async_set_updated_data({"system": {"devices_data": []}})
        await hass.async_block_till_done()
        coordinator.async_set_updated_data({"system": {"devices_data": []}})
        await hass.async_block_till_done()

    add_entities.assert_called_once_with(["sensor"])
    assert coordinator.update_interval is None
    assert not coordinator._listeners


async def test_daily_sensors_keep_configured_interval(hass, daily_setup):
    entry, coordinator = daily_setup
    coordinator.update_interval = timedelta(hours=6)
    async_add_daily_sensors_when_ready(hass, entry, coordinator, mock.Mock())
    assert coordinator.update_interval == DAILY_SENSORS_RETRY_INTERVAL
    coordinator.async_set_updated_data({})
    await hass.async_block_till_done()
    assert coordinator.update_interval == timedelta(hours=6)
    assert not coordinator._listeners


async def test_daily_listener_removed_on_unload(hass, daily_setup):
    entry, coordinator = daily_setup
    async_add_daily_sensors_when_ready(hass, entry, coordinator, mock.Mock())
    for unload in entry._on_unload:
        unload()
    assert not coordinator._listeners


@pytest.fixture
def entry(hass):
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={"username": "u", "password": "p"}, options={}
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def api_class():
    with mock.patch("custom_components.mypyllant.MyPyllantAPI") as api:
        api.return_value.login = mock.AsyncMock()
        api.return_value.aiohttp_session.close = mock.AsyncMock()
        yield api


def login_error_503() -> LoginEndpointInvalid:
    error = LoginEndpointInvalid()
    error.__cause__ = ClientResponseError(
        request_info=mock.Mock(), history=(), status=503, message="Unavailable"
    )
    return error


@pytest.mark.parametrize(
    "error",
    [login_error_503(), TimeoutError(), Exception({"error": "server_error"})],
)
async def test_transient_login_error_retries(hass, entry, api_class, error):
    api_class.return_value.login.side_effect = error
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)
    api_class.return_value.aiohttp_session.close.assert_awaited_once()
    recovery = await SetupRecovery.async_get(hass, entry.entry_id)
    assert recovery.next_setup_attempt()


async def test_rejected_credentials_ask_for_reauth(hass, entry, api_class):
    api_class.return_value.login.side_effect = AuthenticationFailed("Login failed")
    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, entry)
    api_class.return_value.aiohttp_session.close.assert_awaited_once()


async def test_setup_makes_no_api_call_while_paused(hass, entry, api_class):
    recovery = await SetupRecovery.async_get(hass, entry.entry_id)
    recovery.set_blocked(
        SYSTEM_COORDINATOR, datetime.now(timezone.utc) + timedelta(days=2)
    )
    with pytest.raises(ConfigEntryNotReady, match="paused until"):
        await async_setup_entry(hass, entry)
    api_class.assert_not_called()


async def test_failed_system_refresh_backs_off(hass, entry, api_class):
    async def failed_refresh(coordinator):
        coordinator.last_update_success = False

    with mock.patch.object(SystemCoordinator, "async_refresh", failed_refresh):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)
    api_class.return_value.aiohttp_session.close.assert_awaited_once()
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_backoff_doubles_and_is_capped(hass, entry):
    recovery = await SetupRecovery.async_get(hass, entry.entry_id)
    delays = [recovery.record_setup_failure() for _ in range(8)]
    assert delays[:2] == [API_DOWN_PAUSE_INTERVAL, API_DOWN_PAUSE_INTERVAL * 2]
    assert delays[-1] == SETUP_MAX_BACKOFF
    recovery.record_setup_success()
    assert recovery.next_setup_attempt() is None


async def test_quota_block_survives_restart(hass, hass_storage, entry):
    recovery = await SetupRecovery.async_get(hass, entry.entry_id)
    hass.data[DOMAIN] = {entry.entry_id: {"recovery": recovery}}
    coordinator = DailyDataCoordinator(hass, mock.Mock(), entry, None)
    with pytest.raises(UpdateFailed):
        coordinator._set_quota_and_raise(quota_error("5.12:32:57"))
    await recovery._store.async_save(recovery._data)

    hass.data.pop(RECOVERY_INSTANCES)
    restored = await SetupRecovery.async_get(hass, entry.entry_id)
    hass.data[DOMAIN] = {entry.entry_id: {"recovery": restored}}
    after_restart = DailyDataCoordinator(hass, mock.Mock(), entry, None)
    with pytest.raises(UpdateFailed, match="skipping update"):
        after_restart._raise_if_quota_hit()


async def test_zero_quota_duration_is_not_default_pause(hass, entry):
    hass.data[DOMAIN] = {entry.entry_id: {}}
    coordinator = DailyDataCoordinator(hass, mock.Mock(), entry, None)
    coordinator._set_quota_and_raise(quota_error("00:00:00"))
    assert coordinator._quota_hit_time is None


async def test_http_429_is_treated_as_quota():
    error = ClientResponseError(
        request_info=mock.Mock(),
        history=(),
        status=429,
        message="Too many requests",
        headers={"Retry-After": "120"},
    )
    assert extract_quota_duration(error) == 120


async def test_ambisense_error_keeps_system_data(hass, entry):
    hass.data[DOMAIN] = {entry.entry_id: {}}
    entry = mock.Mock(entry_id=entry.entry_id, options={"fetch_ambisense_rooms": True})
    coordinator = SystemCoordinator(hass, mock.Mock(), entry, None)
    coordinator.homes = [mock.Mock()]
    coordinator._refresh_session = mock.AsyncMock()
    systems = [mock.Mock()]

    async def rooms_fail():
        raise AmbisenseNoFacilityError("no facility")
        yield

    async def ok():
        for system in systems:
            yield system

    coordinator.api.get_systems.side_effect = [rooms_fail(), ok()]
    assert await coordinator._async_update_data() == systems
    assert coordinator.api.get_systems.call_args.args[4] is False
