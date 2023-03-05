import datetime

from myPyllant.models import (
    Circuit,
    Device,
    DeviceData,
    DeviceDataBucket,
    DeviceDataBucketResolution,
    DHWCurrentSpecialFunction,
    DHWOperationMode,
    DomesticHotWater,
    System,
    Zone,
    ZoneCurrentSpecialFunction,
    ZoneHeatingOperatingMode,
    ZoneHeatingState,
)

data = [
    [
        DeviceData(
            device=Device(
                system=System(
                    id="systemId1",
                    status={"online": True, "error": False},
                    devices=[
                        {
                            "device_id": "deviceId3",
                            "serial_number": "serialNumber3",
                            "article_number": "0020260951",
                            "name": "sensoHOME",
                            "type": "CONTROL",
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                        },
                        {
                            "device_id": "deviceId1",
                            "serial_number": "serialNumber1",
                            "article_number": "articleNumber1",
                            "name": "ecoTEC",
                            "type": "HEAT_GENERATOR",
                            "operational_data": {
                                "water_pressure": {
                                    "value": 1.2,
                                    "unit": "BAR",
                                    "step_size": 0.1,
                                }
                            },
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                            "properties": ["EMF"],
                        },
                    ],
                    current_system={
                        "system_type": "BOILER_OR_ELECTRIC_HEATER",
                        "primary_heat_generator": {
                            "device_uuid": "dccead04-836b-5d5f-a5ca-dc790a6f0167",
                            "ebus_id": "BAI00",
                            "spn": 376,
                            "bus_coupler_address": 0,
                            "article_number": "articleNumber1",
                            "emfValid": True,
                            "device_serial_number": "serialNumber1",
                            "device_type": "BOILER",
                            "first_data": "2022-12-14T15:19:55Z",
                            "last_data": "2023-03-05T17:51:36Z",
                            "data": [
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                            ],
                            "product_name": "VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                        },
                        "secondary_heat_generators": [],
                        "electric_backup_heater": None,
                        "solar_station": None,
                        "ventilation": None,
                    },
                    system_configuration={"time_zone_id": "Europe/Madrid"},
                    system_control_state={
                        "control_identifier": "TLI",
                        "control_state": {
                            "zones": [
                                {
                                    "name": "Zone 1",
                                    "index": 0,
                                    "active": True,
                                    "desired_room_temperature_setpoint": 0.0,
                                    "current_room_temperature": 19.5,
                                    "heating_operation_mode": "OFF",
                                    "current_special_function": "NONE",
                                    "heating_state": "IDLE",
                                    "set_back_temperature": 10.0,
                                    "manual_mode_setpoint": 16.0,
                                    "time_windows": {
                                        "heating": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 12,
                                                "set_point_required_per_slot": True,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "23:30",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "circuits": [
                                {
                                    "index": 0,
                                    "zones": [],
                                    "set_back_mode_enabled": False,
                                    "circuit_state": "STANDBY",
                                    "current_circuit_flow_temperature": 19.5,
                                    "mixer_circuit_type_external": "HEATING",
                                    "is_cooling_allowed": False,
                                }
                            ],
                            "domestic_hot_water": [
                                {
                                    "index": 255,
                                    "set_point": 45.0,
                                    "current_special_function": "REGULAR",
                                    "operation_mode": "OFF",
                                    "min_set_point": 35.0,
                                    "max_set_point": 65.0,
                                    "time_windows": {
                                        "dhw": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 3,
                                                "set_point_required_per_slot": False,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "23:30",
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "properties": {
                                "control_type": "VRT380",
                                "general": {"is_cooling_allowed": False},
                                "circuits": [
                                    {
                                        "index": 0,
                                        "mixer_circuit_type_external": "HEATING",
                                        "is_cooling_allowed": False,
                                    }
                                ],
                            },
                            "general": {
                                "system_mode": "REGULAR",
                                "system_water_pressure": 1.2000000476837158,
                            },
                        },
                    },
                    gateway={
                        "device_id": "deviceId2",
                        "serial_number": "serialNumber2",
                        "system_id": "systemId1",
                        "diagnostic_trouble_codes": [],
                    },
                    has_ownership=True,
                    zones=[
                        Zone(
                            system_id="systemId1",
                            name="Zone 1",
                            index=0,
                            active=True,
                            current_room_temperature=19.5,
                            current_special_function=ZoneCurrentSpecialFunction.NONE,
                            desired_room_temperature_setpoint=0.0,
                            manual_mode_setpoint=16.0,
                            heating_operation_mode=ZoneHeatingOperatingMode.OFF,
                            heating_state=ZoneHeatingState.IDLE,
                            humidity=None,
                            set_back_temperature=10.0,
                            time_windows={
                                "heating": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 12,
                                        "set_point_required_per_slot": True,
                                    },
                                    "monday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "tuesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "wednesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "thursday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "friday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "saturday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "23:30",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "sunday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                }
                            },
                        )
                    ],
                    circuits=[
                        Circuit(
                            system_id="systemId1",
                            index=0,
                            circuit_state="STANDBY",
                            current_circuit_flow_temperature=19.5,
                            heating_curve=None,
                            is_cooling_allowed=False,
                            min_flow_temperature_setpoint=None,
                            mixer_circuit_type_external="HEATING",
                            set_back_mode_enabled=False,
                            zones=[],
                        )
                    ],
                    domestic_hot_water=[
                        DomesticHotWater(
                            system_id="systemId1",
                            index=255,
                            current_dhw_tank_temperature=None,
                            current_special_function=DHWCurrentSpecialFunction.REGULAR,
                            max_set_point=65.0,
                            min_set_point=35.0,
                            operation_mode=DHWOperationMode.OFF,
                            set_point=45.0,
                            time_windows={
                                "dhw": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 3,
                                        "set_point_required_per_slot": False,
                                    },
                                    "monday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "tuesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "wednesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "thursday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "friday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "saturday": [
                                        {"start_time": "07:00", "end_time": "23:30"}
                                    ],
                                    "sunday": [
                                        {"start_time": "07:00", "end_time": "22:00"}
                                    ],
                                }
                            },
                        )
                    ],
                ),
                device_uuid="dccead04-836b-5d5f-a5ca-dc790a6f0167",
                name="ecoTEC",
                product_name="VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                diagnostic_trouble_codes=[],
                properties=[],
                ebus_id="BAI00",
                article_number="articleNumber1",
                device_serial_number="serialNumber1",
                device_type="BOILER",
                first_data=datetime.datetime(
                    2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                ),
                last_data=datetime.datetime(
                    2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                ),
                operational_data={
                    "water_pressure": {"value": 1.2, "unit": "BAR", "step_size": 0.1}
                },
                data=[
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                ],
            ),
            data_from=None,
            data_to=None,
            start_date=datetime.datetime(
                2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            end_date=datetime.datetime(2023, 3, 6, 0, 0, tzinfo=datetime.timezone.utc),
            resolution=DeviceDataBucketResolution.HOUR,
            operation_mode="DOMESTIC_HOT_WATER",
            energy_type="CONSUMED_ELECTRICAL_ENERGY",
            value_type=None,
            data=[
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 18, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
            ],
        ),
        DeviceData(
            device=Device(
                system=System(
                    id="systemId1",
                    status={"online": True, "error": False},
                    devices=[
                        {
                            "device_id": "deviceId3",
                            "serial_number": "serialNumber3",
                            "article_number": "0020260951",
                            "name": "sensoHOME",
                            "type": "CONTROL",
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                        },
                        {
                            "device_id": "deviceId1",
                            "serial_number": "serialNumber1",
                            "article_number": "articleNumber1",
                            "name": "ecoTEC",
                            "type": "HEAT_GENERATOR",
                            "operational_data": {
                                "water_pressure": {
                                    "value": 1.2,
                                    "unit": "BAR",
                                    "step_size": 0.1,
                                }
                            },
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                            "properties": ["EMF"],
                        },
                    ],
                    current_system={
                        "system_type": "BOILER_OR_ELECTRIC_HEATER",
                        "primary_heat_generator": {
                            "device_uuid": "dccead04-836b-5d5f-a5ca-dc790a6f0167",
                            "ebus_id": "BAI00",
                            "spn": 376,
                            "bus_coupler_address": 0,
                            "article_number": "articleNumber1",
                            "emfValid": True,
                            "device_serial_number": "serialNumber1",
                            "device_type": "BOILER",
                            "first_data": "2022-12-14T15:19:55Z",
                            "last_data": "2023-03-05T17:51:36Z",
                            "data": [
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                            ],
                            "product_name": "VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                        },
                        "secondary_heat_generators": [],
                        "electric_backup_heater": None,
                        "solar_station": None,
                        "ventilation": None,
                    },
                    system_configuration={"time_zone_id": "Europe/Madrid"},
                    system_control_state={
                        "control_identifier": "TLI",
                        "control_state": {
                            "zones": [
                                {
                                    "name": "Zone 1",
                                    "index": 0,
                                    "active": True,
                                    "desired_room_temperature_setpoint": 0.0,
                                    "current_room_temperature": 19.5,
                                    "heating_operation_mode": "OFF",
                                    "current_special_function": "NONE",
                                    "heating_state": "IDLE",
                                    "set_back_temperature": 10.0,
                                    "manual_mode_setpoint": 16.0,
                                    "time_windows": {
                                        "heating": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 12,
                                                "set_point_required_per_slot": True,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "23:30",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "circuits": [
                                {
                                    "index": 0,
                                    "zones": [],
                                    "set_back_mode_enabled": False,
                                    "circuit_state": "STANDBY",
                                    "current_circuit_flow_temperature": 19.5,
                                    "mixer_circuit_type_external": "HEATING",
                                    "is_cooling_allowed": False,
                                }
                            ],
                            "domestic_hot_water": [
                                {
                                    "index": 255,
                                    "set_point": 45.0,
                                    "current_special_function": "REGULAR",
                                    "operation_mode": "OFF",
                                    "min_set_point": 35.0,
                                    "max_set_point": 65.0,
                                    "time_windows": {
                                        "dhw": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 3,
                                                "set_point_required_per_slot": False,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "23:30",
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "properties": {
                                "control_type": "VRT380",
                                "general": {"is_cooling_allowed": False},
                                "circuits": [
                                    {
                                        "index": 0,
                                        "mixer_circuit_type_external": "HEATING",
                                        "is_cooling_allowed": False,
                                    }
                                ],
                            },
                            "general": {
                                "system_mode": "REGULAR",
                                "system_water_pressure": 1.2000000476837158,
                            },
                        },
                    },
                    gateway={
                        "device_id": "deviceId2",
                        "serial_number": "serialNumber2",
                        "system_id": "systemId1",
                        "diagnostic_trouble_codes": [],
                    },
                    has_ownership=True,
                    zones=[
                        Zone(
                            system_id="systemId1",
                            name="Zone 1",
                            index=0,
                            active=True,
                            current_room_temperature=19.5,
                            current_special_function=ZoneCurrentSpecialFunction.NONE,
                            desired_room_temperature_setpoint=0.0,
                            manual_mode_setpoint=16.0,
                            heating_operation_mode=ZoneHeatingOperatingMode.OFF,
                            heating_state=ZoneHeatingState.IDLE,
                            humidity=None,
                            set_back_temperature=10.0,
                            time_windows={
                                "heating": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 12,
                                        "set_point_required_per_slot": True,
                                    },
                                    "monday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "tuesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "wednesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "thursday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "friday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "saturday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "23:30",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "sunday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                }
                            },
                        )
                    ],
                    circuits=[
                        Circuit(
                            system_id="systemId1",
                            index=0,
                            circuit_state="STANDBY",
                            current_circuit_flow_temperature=19.5,
                            heating_curve=None,
                            is_cooling_allowed=False,
                            min_flow_temperature_setpoint=None,
                            mixer_circuit_type_external="HEATING",
                            set_back_mode_enabled=False,
                            zones=[],
                        )
                    ],
                    domestic_hot_water=[
                        DomesticHotWater(
                            system_id="systemId1",
                            index=255,
                            current_dhw_tank_temperature=None,
                            current_special_function=DHWCurrentSpecialFunction.REGULAR,
                            max_set_point=65.0,
                            min_set_point=35.0,
                            operation_mode=DHWOperationMode.OFF,
                            set_point=45.0,
                            time_windows={
                                "dhw": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 3,
                                        "set_point_required_per_slot": False,
                                    },
                                    "monday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "tuesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "wednesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "thursday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "friday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "saturday": [
                                        {"start_time": "07:00", "end_time": "23:30"}
                                    ],
                                    "sunday": [
                                        {"start_time": "07:00", "end_time": "22:00"}
                                    ],
                                }
                            },
                        )
                    ],
                ),
                device_uuid="dccead04-836b-5d5f-a5ca-dc790a6f0167",
                name="ecoTEC",
                product_name="VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                diagnostic_trouble_codes=[],
                properties=[],
                ebus_id="BAI00",
                article_number="articleNumber1",
                device_serial_number="serialNumber1",
                device_type="BOILER",
                first_data=datetime.datetime(
                    2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                ),
                last_data=datetime.datetime(
                    2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                ),
                operational_data={
                    "water_pressure": {"value": 1.2, "unit": "BAR", "step_size": 0.1}
                },
                data=[
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                ],
            ),
            data_from=None,
            data_to=None,
            start_date=datetime.datetime(
                2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            end_date=datetime.datetime(2023, 3, 6, 0, 0, tzinfo=datetime.timezone.utc),
            resolution=DeviceDataBucketResolution.HOUR,
            operation_mode="HEATING",
            energy_type="CONSUMED_ELECTRICAL_ENERGY",
            value_type=None,
            data=[
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=64.23828,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=64.07031,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=63.6875,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=62.23047,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=63.878906,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=63.890625,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=63.726562,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=58.464844,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=27.605469,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.4414062,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3.6484375,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.203125,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.1992188,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.1992188,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.1992188,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.2109375,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=2.1992188,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 18, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=1.890625,
                ),
            ],
        ),
        DeviceData(
            device=Device(
                system=System(
                    id="systemId1",
                    status={"online": True, "error": False},
                    devices=[
                        {
                            "device_id": "deviceId3",
                            "serial_number": "serialNumber3",
                            "article_number": "0020260951",
                            "name": "sensoHOME",
                            "type": "CONTROL",
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                        },
                        {
                            "device_id": "deviceId1",
                            "serial_number": "serialNumber1",
                            "article_number": "articleNumber1",
                            "name": "ecoTEC",
                            "type": "HEAT_GENERATOR",
                            "operational_data": {
                                "water_pressure": {
                                    "value": 1.2,
                                    "unit": "BAR",
                                    "step_size": 0.1,
                                }
                            },
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                            "properties": ["EMF"],
                        },
                    ],
                    current_system={
                        "system_type": "BOILER_OR_ELECTRIC_HEATER",
                        "primary_heat_generator": {
                            "device_uuid": "dccead04-836b-5d5f-a5ca-dc790a6f0167",
                            "ebus_id": "BAI00",
                            "spn": 376,
                            "bus_coupler_address": 0,
                            "article_number": "articleNumber1",
                            "emfValid": True,
                            "device_serial_number": "serialNumber1",
                            "device_type": "BOILER",
                            "first_data": "2022-12-14T15:19:55Z",
                            "last_data": "2023-03-05T17:51:36Z",
                            "data": [
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                            ],
                            "product_name": "VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                        },
                        "secondary_heat_generators": [],
                        "electric_backup_heater": None,
                        "solar_station": None,
                        "ventilation": None,
                    },
                    system_configuration={"time_zone_id": "Europe/Madrid"},
                    system_control_state={
                        "control_identifier": "TLI",
                        "control_state": {
                            "zones": [
                                {
                                    "name": "Zone 1",
                                    "index": 0,
                                    "active": True,
                                    "desired_room_temperature_setpoint": 0.0,
                                    "current_room_temperature": 19.5,
                                    "heating_operation_mode": "OFF",
                                    "current_special_function": "NONE",
                                    "heating_state": "IDLE",
                                    "set_back_temperature": 10.0,
                                    "manual_mode_setpoint": 16.0,
                                    "time_windows": {
                                        "heating": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 12,
                                                "set_point_required_per_slot": True,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "23:30",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "circuits": [
                                {
                                    "index": 0,
                                    "zones": [],
                                    "set_back_mode_enabled": False,
                                    "circuit_state": "STANDBY",
                                    "current_circuit_flow_temperature": 19.5,
                                    "mixer_circuit_type_external": "HEATING",
                                    "is_cooling_allowed": False,
                                }
                            ],
                            "domestic_hot_water": [
                                {
                                    "index": 255,
                                    "set_point": 45.0,
                                    "current_special_function": "REGULAR",
                                    "operation_mode": "OFF",
                                    "min_set_point": 35.0,
                                    "max_set_point": 65.0,
                                    "time_windows": {
                                        "dhw": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 3,
                                                "set_point_required_per_slot": False,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "23:30",
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "properties": {
                                "control_type": "VRT380",
                                "general": {"is_cooling_allowed": False},
                                "circuits": [
                                    {
                                        "index": 0,
                                        "mixer_circuit_type_external": "HEATING",
                                        "is_cooling_allowed": False,
                                    }
                                ],
                            },
                            "general": {
                                "system_mode": "REGULAR",
                                "system_water_pressure": 1.2000000476837158,
                            },
                        },
                    },
                    gateway={
                        "device_id": "deviceId2",
                        "serial_number": "serialNumber2",
                        "system_id": "systemId1",
                        "diagnostic_trouble_codes": [],
                    },
                    has_ownership=True,
                    zones=[
                        Zone(
                            system_id="systemId1",
                            name="Zone 1",
                            index=0,
                            active=True,
                            current_room_temperature=19.5,
                            current_special_function=ZoneCurrentSpecialFunction.NONE,
                            desired_room_temperature_setpoint=0.0,
                            manual_mode_setpoint=16.0,
                            heating_operation_mode=ZoneHeatingOperatingMode.OFF,
                            heating_state=ZoneHeatingState.IDLE,
                            humidity=None,
                            set_back_temperature=10.0,
                            time_windows={
                                "heating": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 12,
                                        "set_point_required_per_slot": True,
                                    },
                                    "monday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "tuesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "wednesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "thursday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "friday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "saturday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "23:30",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "sunday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                }
                            },
                        )
                    ],
                    circuits=[
                        Circuit(
                            system_id="systemId1",
                            index=0,
                            circuit_state="STANDBY",
                            current_circuit_flow_temperature=19.5,
                            heating_curve=None,
                            is_cooling_allowed=False,
                            min_flow_temperature_setpoint=None,
                            mixer_circuit_type_external="HEATING",
                            set_back_mode_enabled=False,
                            zones=[],
                        )
                    ],
                    domestic_hot_water=[
                        DomesticHotWater(
                            system_id="systemId1",
                            index=255,
                            current_dhw_tank_temperature=None,
                            current_special_function=DHWCurrentSpecialFunction.REGULAR,
                            max_set_point=65.0,
                            min_set_point=35.0,
                            operation_mode=DHWOperationMode.OFF,
                            set_point=45.0,
                            time_windows={
                                "dhw": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 3,
                                        "set_point_required_per_slot": False,
                                    },
                                    "monday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "tuesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "wednesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "thursday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "friday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "saturday": [
                                        {"start_time": "07:00", "end_time": "23:30"}
                                    ],
                                    "sunday": [
                                        {"start_time": "07:00", "end_time": "22:00"}
                                    ],
                                }
                            },
                        )
                    ],
                ),
                device_uuid="dccead04-836b-5d5f-a5ca-dc790a6f0167",
                name="ecoTEC",
                product_name="VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                diagnostic_trouble_codes=[],
                properties=[],
                ebus_id="BAI00",
                article_number="articleNumber1",
                device_serial_number="serialNumber1",
                device_type="BOILER",
                first_data=datetime.datetime(
                    2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                ),
                last_data=datetime.datetime(
                    2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                ),
                operational_data={
                    "water_pressure": {"value": 1.2, "unit": "BAR", "step_size": 0.1}
                },
                data=[
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                ],
            ),
            data_from=None,
            data_to=None,
            start_date=datetime.datetime(
                2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            end_date=datetime.datetime(2023, 3, 6, 0, 0, tzinfo=datetime.timezone.utc),
            resolution=DeviceDataBucketResolution.HOUR,
            operation_mode="DOMESTIC_HOT_WATER",
            energy_type="CONSUMED_PRIMARY_ENERGY",
            value_type=None,
            data=[
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 18, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
            ],
        ),
        DeviceData(
            device=Device(
                system=System(
                    id="systemId1",
                    status={"online": True, "error": False},
                    devices=[
                        {
                            "device_id": "deviceId3",
                            "serial_number": "serialNumber3",
                            "article_number": "0020260951",
                            "name": "sensoHOME",
                            "type": "CONTROL",
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                        },
                        {
                            "device_id": "deviceId1",
                            "serial_number": "serialNumber1",
                            "article_number": "articleNumber1",
                            "name": "ecoTEC",
                            "type": "HEAT_GENERATOR",
                            "operational_data": {
                                "water_pressure": {
                                    "value": 1.2,
                                    "unit": "BAR",
                                    "step_size": 0.1,
                                }
                            },
                            "system_id": "systemId1",
                            "diagnostic_trouble_codes": [],
                            "properties": ["EMF"],
                        },
                    ],
                    current_system={
                        "system_type": "BOILER_OR_ELECTRIC_HEATER",
                        "primary_heat_generator": {
                            "device_uuid": "dccead04-836b-5d5f-a5ca-dc790a6f0167",
                            "ebus_id": "BAI00",
                            "spn": 376,
                            "bus_coupler_address": 0,
                            "article_number": "articleNumber1",
                            "emfValid": True,
                            "device_serial_number": "serialNumber1",
                            "device_type": "BOILER",
                            "first_data": "2022-12-14T15:19:55Z",
                            "last_data": "2023-03-05T17:51:36Z",
                            "data": [
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_ELECTRICAL_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:55Z",
                                    "to": "2023-03-05T17:51:35Z",
                                },
                                {
                                    "operation_mode": "DOMESTIC_HOT_WATER",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                                {
                                    "operation_mode": "HEATING",
                                    "value_type": "CONSUMED_PRIMARY_ENERGY",
                                    "calculated": False,
                                    "from": "2022-12-14T15:19:56Z",
                                    "to": "2023-03-05T17:51:36Z",
                                },
                            ],
                            "product_name": "VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                        },
                        "secondary_heat_generators": [],
                        "electric_backup_heater": None,
                        "solar_station": None,
                        "ventilation": None,
                    },
                    system_configuration={"time_zone_id": "Europe/Madrid"},
                    system_control_state={
                        "control_identifier": "TLI",
                        "control_state": {
                            "zones": [
                                {
                                    "name": "Zone 1",
                                    "index": 0,
                                    "active": True,
                                    "desired_room_temperature_setpoint": 0.0,
                                    "current_room_temperature": 19.5,
                                    "heating_operation_mode": "OFF",
                                    "current_special_function": "NONE",
                                    "heating_state": "IDLE",
                                    "set_back_temperature": 10.0,
                                    "manual_mode_setpoint": 16.0,
                                    "time_windows": {
                                        "heating": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 12,
                                                "set_point_required_per_slot": True,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:00",
                                                    "end_time": "20:30",
                                                    "set_point": 21.0,
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "06:00",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "23:30",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:30",
                                                    "end_time": "22:00",
                                                    "set_point": 20.0,
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "circuits": [
                                {
                                    "index": 0,
                                    "zones": [],
                                    "set_back_mode_enabled": False,
                                    "circuit_state": "STANDBY",
                                    "current_circuit_flow_temperature": 19.5,
                                    "mixer_circuit_type_external": "HEATING",
                                    "is_cooling_allowed": False,
                                }
                            ],
                            "domestic_hot_water": [
                                {
                                    "index": 255,
                                    "set_point": 45.0,
                                    "current_special_function": "REGULAR",
                                    "operation_mode": "OFF",
                                    "min_set_point": 35.0,
                                    "max_set_point": 65.0,
                                    "time_windows": {
                                        "dhw": {
                                            "meta_info": {
                                                "min_slots_per_day": 0,
                                                "max_slots_per_day": 3,
                                                "set_point_required_per_slot": False,
                                            },
                                            "monday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "tuesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "wednesday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "thursday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "friday": [
                                                {
                                                    "start_time": "05:30",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                            "saturday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "23:30",
                                                }
                                            ],
                                            "sunday": [
                                                {
                                                    "start_time": "07:00",
                                                    "end_time": "22:00",
                                                }
                                            ],
                                        }
                                    },
                                }
                            ],
                            "properties": {
                                "control_type": "VRT380",
                                "general": {"is_cooling_allowed": False},
                                "circuits": [
                                    {
                                        "index": 0,
                                        "mixer_circuit_type_external": "HEATING",
                                        "is_cooling_allowed": False,
                                    }
                                ],
                            },
                            "general": {
                                "system_mode": "REGULAR",
                                "system_water_pressure": 1.2000000476837158,
                            },
                        },
                    },
                    gateway={
                        "device_id": "deviceId2",
                        "serial_number": "serialNumber2",
                        "system_id": "systemId1",
                        "diagnostic_trouble_codes": [],
                    },
                    has_ownership=True,
                    zones=[
                        Zone(
                            system_id="systemId1",
                            name="Zone 1",
                            index=0,
                            active=True,
                            current_room_temperature=19.5,
                            current_special_function=ZoneCurrentSpecialFunction.NONE,
                            desired_room_temperature_setpoint=0.0,
                            manual_mode_setpoint=16.0,
                            heating_operation_mode=ZoneHeatingOperatingMode.OFF,
                            heating_state=ZoneHeatingState.IDLE,
                            humidity=None,
                            set_back_temperature=10.0,
                            time_windows={
                                "heating": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 12,
                                        "set_point_required_per_slot": True,
                                    },
                                    "monday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "tuesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "wednesday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "thursday": [
                                        {
                                            "start_time": "05:00",
                                            "end_time": "20:30",
                                            "set_point": 21.0,
                                        }
                                    ],
                                    "friday": [
                                        {
                                            "start_time": "06:00",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "saturday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "23:30",
                                            "set_point": 20.0,
                                        }
                                    ],
                                    "sunday": [
                                        {
                                            "start_time": "07:30",
                                            "end_time": "22:00",
                                            "set_point": 20.0,
                                        }
                                    ],
                                }
                            },
                        )
                    ],
                    circuits=[
                        Circuit(
                            system_id="systemId1",
                            index=0,
                            circuit_state="STANDBY",
                            current_circuit_flow_temperature=19.5,
                            heating_curve=None,
                            is_cooling_allowed=False,
                            min_flow_temperature_setpoint=None,
                            mixer_circuit_type_external="HEATING",
                            set_back_mode_enabled=False,
                            zones=[],
                        )
                    ],
                    domestic_hot_water=[
                        DomesticHotWater(
                            system_id="systemId1",
                            index=255,
                            current_dhw_tank_temperature=None,
                            current_special_function=DHWCurrentSpecialFunction.REGULAR,
                            max_set_point=65.0,
                            min_set_point=35.0,
                            operation_mode=DHWOperationMode.OFF,
                            set_point=45.0,
                            time_windows={
                                "dhw": {
                                    "meta_info": {
                                        "min_slots_per_day": 0,
                                        "max_slots_per_day": 3,
                                        "set_point_required_per_slot": False,
                                    },
                                    "monday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "tuesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "wednesday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "thursday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "friday": [
                                        {"start_time": "05:30", "end_time": "22:00"}
                                    ],
                                    "saturday": [
                                        {"start_time": "07:00", "end_time": "23:30"}
                                    ],
                                    "sunday": [
                                        {"start_time": "07:00", "end_time": "22:00"}
                                    ],
                                }
                            },
                        )
                    ],
                ),
                device_uuid="dccead04-836b-5d5f-a5ca-dc790a6f0167",
                name="ecoTEC",
                product_name="VMW 32CS/1-5 C (N-ES) ecoTEC plus",
                diagnostic_trouble_codes=[],
                properties=[],
                ebus_id="BAI00",
                article_number="articleNumber1",
                device_serial_number="serialNumber1",
                device_type="BOILER",
                first_data=datetime.datetime(
                    2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                ),
                last_data=datetime.datetime(
                    2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                ),
                operational_data={
                    "water_pressure": {"value": 1.2, "unit": "BAR", "step_size": 0.1}
                },
                data=[
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 55, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 35, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_ELECTRICAL_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="DOMESTIC_HOT_WATER",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                    DeviceData(
                        device=None,
                        data_from=datetime.datetime(
                            2022, 12, 14, 15, 19, 56, tzinfo=datetime.timezone.utc
                        ),
                        data_to=datetime.datetime(
                            2023, 3, 5, 17, 51, 36, tzinfo=datetime.timezone.utc
                        ),
                        start_date=None,
                        end_date=None,
                        resolution=None,
                        operation_mode="HEATING",
                        energy_type=None,
                        value_type="CONSUMED_PRIMARY_ENERGY",
                        data=[],
                    ),
                ],
            ),
            data_from=None,
            data_to=None,
            start_date=datetime.datetime(
                2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            end_date=datetime.datetime(2023, 3, 6, 0, 0, tzinfo=datetime.timezone.utc),
            resolution=DeviceDataBucketResolution.HOUR,
            operation_mode="HEATING",
            energy_type="CONSUMED_PRIMARY_ENERGY",
            value_type=None,
            data=[
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=4664.75,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 1, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=4257.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 2, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3968.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 3, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3806.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 4, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3761.5,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 5, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3785.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 6, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3733.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 7, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=3241.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 8, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=1096.5,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 9, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 10, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 11, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 12, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 13, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 14, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 15, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 16, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
                DeviceDataBucket(
                    start_date=datetime.datetime(
                        2023, 3, 5, 17, 0, tzinfo=datetime.timezone.utc
                    ),
                    end_date=datetime.datetime(
                        2023, 3, 5, 18, 0, tzinfo=datetime.timezone.utc
                    ),
                    value=0.0,
                ),
            ],
        ),
    ]
]
