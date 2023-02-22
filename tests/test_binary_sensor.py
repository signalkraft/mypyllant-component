from myPyllant.models import System

from custom_components.mypyllant.binary_sensor import CircuitEntity, SystemControlEntity


async def test_system_sensors(hass, system_coordinator_mock):
    system = SystemControlEntity(0, system_coordinator_mock)
    assert isinstance(system.device_info, dict)

    circuit = CircuitEntity(0, 0, system_coordinator_mock)
    assert isinstance(circuit.device_info, dict)
    assert isinstance(circuit.system, System)
