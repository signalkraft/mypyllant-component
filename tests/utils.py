from unittest import mock

from custom_components.mypyllant.const import DOMAIN
from custom_components.mypyllant import async_setup_entry
from tests.conftest import MockConfigEntry, TEST_OPTIONS
from tests.test_init import test_user_input


async def call_service(
    service_name,
    service_kwargs,
    hass,
    mypyllant_aioresponses,
    mocked_api,
    system_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator_mock.data = (
            await system_coordinator_mock._async_update_data()
        )
        with mock.patch(
            "custom_components.mypyllant.MyPyllantAPI",
            side_effect=lambda *args, **kwargs: mocked_api,
        ), mock.patch(
            "custom_components.mypyllant.SystemCoordinator",
            side_effect=lambda *args: system_coordinator_mock,
        ), mock.patch("custom_components.mypyllant.PLATFORMS", []):
            config_entry = MockConfigEntry(
                domain=DOMAIN,
                title="Mock Title",
                data=test_user_input,
                options=TEST_OPTIONS,
            )
            config_entry.add_to_hass(hass)
            await async_setup_entry(hass, config_entry)
            await hass.async_block_till_done()
            result = await hass.services.async_call(
                DOMAIN,
                service_name,
                **service_kwargs,
            )
    return result


def get_config_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        title="Mock Title",
        data=test_user_input,
        options=TEST_OPTIONS,
    )
