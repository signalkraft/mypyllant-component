import json

import pytest

from custom_components.mypyllant.const import (
    SERVICE_GENERATE_TEST_DATA,
    SERVICE_EXPORT,
)
from myPyllant.api import MyPyllantAPI
from myPyllant.tests.utils import list_test_data

from tests.utils import call_service


@pytest.mark.parametrize("test_data", list_test_data())
@pytest.mark.enable_socket
async def test_service_generate_test_data(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    result = await call_service(
        SERVICE_GENERATE_TEST_DATA,
        {"blocking": True, "return_response": True},
        hass,
        mypyllant_aioresponses,
        mocked_api,
        system_coordinator_mock,
        test_data,
    )
    if "homes" not in result:
        await mocked_api.aiohttp_session.close()
        pytest.skip("No home data")
    assert "homes" in result
    assert all(h["systemId"] in result for h in result["homes"])
    await mocked_api.aiohttp_session.close()


@pytest.mark.parametrize("test_data", list_test_data())
async def test_service_export(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    result = await call_service(
        SERVICE_EXPORT,
        {"blocking": True, "return_response": True},
        hass,
        mypyllant_aioresponses,
        mocked_api,
        system_coordinator_mock,
        test_data,
    )
    assert isinstance(result, dict)
    assert isinstance(result["export"], list)
    assert "home" in result["export"][0]

    assert isinstance(
        json.dumps(
            result,
            indent=2,
            default=str,
        ),
        str,
    )

    await mocked_api.aiohttp_session.close()
