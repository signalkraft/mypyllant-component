from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mypyllant.const import DOMAIN


test_user_input = {
    "username": "username",
    "password": "password",
    "country": "germany",
    "brand": "vaillant",
}


def get_config_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        title="Mock Title",
        data=test_user_input,
    )
