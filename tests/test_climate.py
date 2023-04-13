from custom_components.mypyllant.climate import ZoneClimate


async def test_climate(hass, system_coordinator_mock):
    climate = ZoneClimate(0, 0, system_coordinator_mock, 3)
    assert isinstance(climate.device_info, dict)
    assert isinstance(climate.target_temperature, float)
    assert isinstance(climate.current_temperature, float)
    assert isinstance(climate.current_humidity, float)
    assert isinstance(climate.preset_modes, list)
    assert climate.hvac_mode in climate.hvac_modes
    assert climate.preset_mode in climate.preset_modes
