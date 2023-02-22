from custom_components.mypyllant.water_heater import DomesticHotWaterEntity


async def test_water_heater(hass, system_coordinator_mock):
    climate = DomesticHotWaterEntity(0, 0, system_coordinator_mock)
    assert isinstance(climate.device_info, dict)
    assert isinstance(climate.target_temperature, float)
    assert isinstance(climate.current_temperature, float)
    assert isinstance(climate.operation_list, list)
    assert climate.current_operation in climate.operation_list
