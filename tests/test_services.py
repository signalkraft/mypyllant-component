import json
from dataclasses import asdict

import pytest
from homeassistant.helpers.entity_registry import DATA_REGISTRY, EntityRegistry
from homeassistant.loader import (
    DATA_COMPONENTS,
    DATA_INTEGRATIONS,
    DATA_PRELOAD_PLATFORMS,
    DATA_MISSING_PLATFORMS,
)

from custom_components.mypyllant import SystemCoordinator
from custom_components.mypyllant.climate import AmbisenseClimate
from custom_components.mypyllant.const import (
    SERVICE_GENERATE_TEST_DATA,
    SERVICE_EXPORT,
    DOMAIN,
)
from myPyllant.api import MyPyllantAPI
from myPyllant.models import RoomTimeProgram
from myPyllant.tests.generate_test_data import DATA_DIR
from myPyllant.tests.utils import list_test_data, load_test_data

from tests.utils import get_config_entry


def setup_hass_for_service_test(hass):
    hass.data[DATA_COMPONENTS] = {}
    hass.data[DATA_INTEGRATIONS] = {}
    hass.data[DATA_PRELOAD_PLATFORMS] = {}
    hass.data[DATA_MISSING_PLATFORMS] = {}
    hass.data[DATA_REGISTRY] = EntityRegistry(hass)
    return hass


@pytest.mark.parametrize("test_data", list_test_data())
async def test_service_generate_test_data(
    hass,
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock,
    test_data,
):
    hass = setup_hass_for_service_test(hass)

    with mypyllant_aioresponses(test_data):
        config_entry = get_config_entry()
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_GENERATE_TEST_DATA,
            blocking=True,
            return_response=True,
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
    hass = setup_hass_for_service_test(hass)

    with mypyllant_aioresponses(test_data):
        config_entry = get_config_entry()
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_EXPORT,
            blocking=True,
            return_response=True,
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


@pytest.mark.parametrize(
    "test_data_path",
    ["ambisense", "ambisense2.yaml"],
)
async def test_ambisense_time_program(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    system_coordinator_mock: SystemCoordinator,
    test_data_path,
) -> None:
    test_data = load_test_data(DATA_DIR / test_data_path)
    with mypyllant_aioresponses(test_data) as aio:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        ambisense = AmbisenseClimate(
            0,
            1,
            system_coordinator_mock,
            get_config_entry(),
            {},
        )
        time_program = asdict(
            ambisense.room.time_program, dict_factory=RoomTimeProgram.dict_factory
        )
        time_program["monday"][0]["setpoint"] = time_program["monday"][0].pop(
            "temperature_setpoint"
        )
        await ambisense.set_time_program(time_program=time_program)
        last_request_key = list(aio.requests.keys())[-1]
        request_url = last_request_key[1]
        request_json = aio.requests[last_request_key][0][1]["json"]
        assert "temperatureSetpoint" in request_json["monday"][0]
        assert str(request_url).endswith(
            f"rooms/{ambisense.room.room_index}/timeprogram"
        )
        time_program["monday"][0]["end_time"] = 1200
        with pytest.raises(ValueError):
            await ambisense.set_time_program(time_program=time_program)
        system_coordinator_mock._debounced_refresh.async_cancel()
    await mocked_api.aiohttp_session.close()
