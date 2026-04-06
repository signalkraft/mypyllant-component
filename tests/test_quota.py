from asyncio import CancelledError
from datetime import datetime, timedelta, timezone

import pytest as pytest
from aiohttp import RequestInfo
from aiohttp.client_exceptions import ClientResponseError
from freezegun import freeze_time
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.mypyllant.utils import extract_quota_duration
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.const import (
    API_DOWN_PAUSE_INTERVAL,
    QUOTA_PAUSE_INTERVAL,
)


async def test_quota(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    # Trigger quota error in the past and check that it raises an exception
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",  # type: ignore
            method="GET",
            headers=None,  # type: ignore
        ),
        history=None,  # type: ignore
        status=403,
        message="Quota Exceeded",
    )
    with freeze_time(
        datetime.now(timezone.utc) - timedelta(seconds=QUOTA_PAUSE_INTERVAL + 180)
    ):
        with mypyllant_aioresponses(raise_exception=quota_exception) as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*") as _:
                system_coordinator_mock.data = (
                    await system_coordinator_mock._async_update_data()
                )

    # Quota error should still raise before the interval is over
    with freeze_time(
        datetime.now(timezone.utc) - timedelta(seconds=QUOTA_PAUSE_INTERVAL / 2)
    ):
        with mypyllant_aioresponses() as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*") as _:
                system_coordinator_mock.data = (
                    await system_coordinator_mock._async_update_data()
                )

    # No more error after interval is over
    with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
    await mocked_api.aiohttp_session.close()


async def test_quota_time_extraction(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",  # type: ignore
            method="GET",
            headers=None,  # type: ignore
        ),
        history=None,  # type: ignore
        status=403,
        message='{ "statusCode": 403, "message": "Out of call volume quota. Quota will be replenished in 00:30:02." }',
    )
    assert extract_quota_duration(quota_exception) == 30 * 60 + 2


async def test_quota_end_time(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    # Trigger quota error in the past with and end time and check that it raises an exception
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",  # type: ignore
            method="GET",
            headers=None,  # type: ignore
        ),
        history=None,  # type: ignore
        status=403,
        message='{ "statusCode": 403, "message": "Out of call volume quota. Quota will be replenished in 00:30:00." }',
    )
    with freeze_time(datetime.now(timezone.utc) - timedelta(seconds=40 * 60)):
        with mypyllant_aioresponses(raise_exception=quota_exception) as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*") as _:
                system_coordinator_mock.data = (
                    await system_coordinator_mock._async_update_data()
                )

    # Quota error should still raise before the interval is over
    with freeze_time(datetime.now(timezone.utc) - timedelta(seconds=30 * 60)):
        with mypyllant_aioresponses() as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*") as _:
                system_coordinator_mock.data = (
                    await system_coordinator_mock._async_update_data()
                )

    # No more error after interval is over
    with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
    await mocked_api.aiohttp_session.close()


async def test_api_down(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    # Trigger API down error and check that it raises an exception
    with mypyllant_aioresponses(raise_exception=CancelledError()) as _:
        with pytest.raises(UpdateFailed, match=r"myVAILLANT API is down.*") as _:
            system_coordinator_mock.data = (
                await system_coordinator_mock._async_update_data()
            )

    # Quota error should still raise before API_DOWN_PAUSE_INTERVAL is over
    with freeze_time(datetime.now(timezone.utc) + timedelta(seconds=10)):
        with mypyllant_aioresponses() as _:
            with pytest.raises(UpdateFailed, match=r"myVAILLANT API is down.*") as _:
                system_coordinator_mock.data = (
                    await system_coordinator_mock._async_update_data()
                )

    # No more error after API_DOWN_PAUSE_INTERVAL is over
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(seconds=(API_DOWN_PAUSE_INTERVAL + 10))
    ):
        with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
            system_coordinator_mock.data = (
                await system_coordinator_mock._async_update_data()
            )
    await mocked_api.aiohttp_session.close()


async def test_quota_state_cleared_after_recovery(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    """After quota backoff expires and a successful fetch, quota state must be fully cleared.

    Regression test: previously, _quota_hit_time was never cleared after recovery,
    causing the coordinator to enter a terminal state where it stopped scheduling
    updates. See https://github.com/signalkraft/mypyllant-component/issues/424
    """
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",
            method="GET",
            headers=None,
        ),
        history=None,
        status=403,
        message='{ "statusCode": 403, "message": "Out of call volume quota. Quota will be replenished in 00:30:00." }',
    )

    # Step 1: Hit quota
    with freeze_time(datetime.now(timezone.utc) - timedelta(seconds=40 * 60)):
        with mypyllant_aioresponses(raise_exception=quota_exception) as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*"):
                await system_coordinator_mock._async_update_data()

    # Verify quota state is set
    assert system_coordinator_mock._quota_hit_time is not None
    assert system_coordinator_mock._quota_end_time is not None
    assert system_coordinator_mock._quota_exc_info is not None

    # Step 2: Recover after backoff expires
    with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )

    # Step 3: Verify quota state is fully cleared
    assert system_coordinator_mock._quota_hit_time is None, (
        "_quota_hit_time should be cleared after successful recovery"
    )
    assert system_coordinator_mock._quota_end_time is None, (
        "_quota_end_time should be cleared after successful recovery"
    )
    assert system_coordinator_mock._quota_exc_info is None, (
        "_quota_exc_info should be cleared after successful recovery"
    )

    # Step 4: A second successful fetch should work without any quota interference
    with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )

    await mocked_api.aiohttp_session.close()


async def test_quota_elapsed_time_uses_total_seconds(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    """Elapsed time must use total_seconds(), not .seconds which wraps at 3600.

    Regression test: .seconds on a timedelta wraps modulo 3600, so a 2-hour
    elapsed time would appear as 0 seconds, incorrectly blocking recovery.
    """
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",
            method="GET",
            headers=None,
        ),
        history=None,
        status=403,
        message="Quota Exceeded",
    )

    # Hit quota far in the past (>1 hour ago, which would wrap with .seconds)
    with freeze_time(
        datetime.now(timezone.utc) - timedelta(hours=2)
    ):
        with mypyllant_aioresponses(raise_exception=quota_exception) as _:
            with pytest.raises(UpdateFailed, match=r"Quota.*"):
                await system_coordinator_mock._async_update_data()

    # After QUOTA_PAUSE_INTERVAL (3 hours), should recover even though
    # .seconds would have wrapped (7200 % 3600 = 0)
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(seconds=QUOTA_PAUSE_INTERVAL + 60)
    ):
        with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
            # This should NOT raise — the backoff period has expired
            system_coordinator_mock.data = (
                await system_coordinator_mock._async_update_data()
            )

    await mocked_api.aiohttp_session.close()


async def test_api_down_state_cleared_after_recovery(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    """After API down backoff expires and recovery succeeds, state must be cleared.

    Regression test: stale _quota_hit_time from API down events was never cleared,
    potentially blocking future updates.
    """
    # Step 1: API goes down
    with mypyllant_aioresponses(raise_exception=CancelledError()) as _:
        with pytest.raises(UpdateFailed, match=r"myVAILLANT API is down.*"):
            await system_coordinator_mock._async_update_data()

    assert system_coordinator_mock._quota_hit_time is not None

    # Step 2: Recover after backoff
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(seconds=(API_DOWN_PAUSE_INTERVAL + 10))
    ):
        with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
            system_coordinator_mock.data = (
                await system_coordinator_mock._async_update_data()
            )

    # Step 3: State should be fully cleared
    assert system_coordinator_mock._quota_hit_time is None, (
        "_quota_hit_time should be cleared after API recovery"
    )
    assert system_coordinator_mock._quota_exc_info is None, (
        "_quota_exc_info should be cleared after API recovery"
    )

    await mocked_api.aiohttp_session.close()


async def test_multiple_quota_hits_then_recovery(
    mypyllant_aioresponses, mocked_api: MyPyllantAPI, system_coordinator_mock
):
    """After multiple consecutive quota errors, coordinator must still recover.

    Regression test: simulates the real-world scenario where 5 consecutive
    quota errors caused the coordinator to enter a terminal state.
    See RCA for incident 2026-04-06.
    """
    quota_exception = ClientResponseError(
        request_info=RequestInfo(
            url="https://api.vaillant-group.com/service-connected-control/end-user-app-api/v1/homes",
            method="GET",
            headers=None,
        ),
        history=None,
        status=403,
        message='{ "statusCode": 403, "message": "Out of call volume quota. Quota will be replenished in 00:10:00." }',
    )

    # Hit quota 5 times in succession (simulating real incident)
    for i in range(5):
        offset = i * 3 * 60  # 3 minutes apart
        with freeze_time(
            datetime.now(timezone.utc) - timedelta(seconds=40 * 60 - offset)
        ):
            with mypyllant_aioresponses(raise_exception=quota_exception) as _:
                with pytest.raises(UpdateFailed, match=r"Quota.*"):
                    await system_coordinator_mock._async_update_data()

    # After all backoff periods expire, coordinator must recover
    with mypyllant_aioresponses(test_data=list_test_data()[0]) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )

    # Quota state must be fully cleared
    assert system_coordinator_mock._quota_hit_time is None
    assert system_coordinator_mock._quota_end_time is None
    assert system_coordinator_mock._quota_exc_info is None

    await mocked_api.aiohttp_session.close()
