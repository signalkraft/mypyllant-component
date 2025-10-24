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
