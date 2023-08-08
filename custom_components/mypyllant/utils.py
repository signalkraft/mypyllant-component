from myPyllant.models import System


def get_system_sensor_unique_id(system: System) -> str:
    """
    If a primary heat generator exists, we use it as a unique id
    Some sensor names are derived from it, so it made sense at the time to use it for the unique id

    Otherwise, we fall back to the system id
    """
    if system.primary_heat_generator:
        return system.primary_heat_generator.device_uuid
    else:
        return system.id
