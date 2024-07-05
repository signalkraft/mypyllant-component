---
description: Available entities and extra attributes in mypyllant-component
hide:
  - navigation
---

# Entities

You can expect these entities, although names will vary based on your home name (here "Home"),
installed devices (in this example "aroTHERM plus" and "Hydraulic Station"),
or the naming of your heating zones (in this case "Zone 1"):

## Sample Entities

| Entity                                                                        | Unit   | Class        | Sample                    |
|-------------------------------------------------------------------------------|--------|--------------|---------------------------|
| Home                                                                          |        |              | 0                         |
| Home Trouble Codes                                                            |        | problem      | off                       |
| Home Online Status                                                            |        | connectivity | on                        |
| Home Firmware Update Required                                                 |        | update       | off                       |
| Home Firmware Update Enabled                                                  |        |              | on                        |
| Home EEBUS Enabled                                                            |        |              | off                       |
| Home EEBUS Capable                                                            |        |              | on                        |
| Home Circuit 0 Cooling Allowed                                                |        |              | on                        |
| Home Zone 1 (Circuit 0) Manual Cooling Active                                 |        |              | off                       |
| Home Zone 1 (Circuit 0)                                                       |        |              | on                        |
| Home Zone 1 (Circuit 0)                                                       |        |              | on                        |
| Home Domestic Hot Water 0                                                     |        |              | on                        |
| Circulating Water in Home Domestic Hot Water 0                                |        |              | off                       |
| Home Zone 1 (Circuit 0) Climate                                               |        |              | auto                      |
| Home Away Mode Start Date                                                     |        |              | unknown                   |
| Home Away Mode End Date                                                       |        |              | unknown                   |
| Home Manual Cooling Start Date                                                |        |              | unknown                   |
| Home Manual Cooling End Date                                                  |        |              | unknown                   |
| Home Holiday Duration Remaining                                               | d      |              | 0                         |
| Home Zone 1 (Circuit 0) Quick Veto Duration                                   | h      |              | unavailable               |
| Home Outdoor Temperature                                                      | °C     | temperature  | 20.0                      |
| Home System Water Pressure                                                    | bar    | pressure     | 1.7                       |
| Home Firmware Version                                                         |        |              | 0357.40.35                |
| Home Zone 1 (Circuit 0) Desired Temperature                                   | °C     | temperature  | 24.0                      |
| Home Zone 1 (Circuit 0) Current Temperature                                   | °C     | temperature  | 21.5                      |
| Home Zone 1 (Circuit 0) Humidity                                              | %      | humidity     | 58.0                      |
| Home Zone 1 (Circuit 0) Heating Operating Mode                                |        |              | Time Controlled           |
| Home Zone 1 (Circuit 0) Heating State                                         |        |              | Idle                      |
| Home Zone 1 (Circuit 0) Current Special Function                              |        |              | None                      |
| Home Circuit 0 State                                                          |        |              | STANDBY                   |
| Home Circuit 0 Current Flow Temperature                                       | °C     | temperature  | 39.0                      |
| Home Circuit 0 Heating Curve                                                  |        |              | 0.82                      |
| Home Domestic Hot Water 0 Tank Temperature                                    | °C     | temperature  | 49.5                      |
| Home Domestic Hot Water 0 Setpoint                                            | °C     | temperature  | 52.0                      |
| Home Domestic Hot Water 0 Operation Mode                                      |        |              | Time Controlled           |
| Home Domestic Hot Water 0 Current Special Function                            |        |              | Regular                   |
| Home Heating Energy Efficiency                                                |        |              | 3.0                       |
| Home Device 0 aroTHERM plus Heating Energy Efficiency                         |        |              | 3.0                       |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Cooling                | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Domestic Hot Water     | Wh     | energy       | 1000.0                    |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Heating                | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Earned Environment Energy Cooling                 | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Earned Environment Energy Domestic Hot Water      | Wh     | energy       | 2000.0                    |
| Home Device 0 aroTHERM plus Earned Environment Energy Heating                 | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Heat Generated Heating                            | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Heat Generated Domestic Hot Water                 | Wh     | energy       | 3000.0                    |
| Home Device 0 aroTHERM plus Heat Generated Cooling                            | Wh     | energy       | 0.0                       |
| Home Device 1 Hydraulic Station Heating Energy Efficiency                     |        |              | unknown                   |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Domestic Hot Water | Wh     | energy       | 0.0                       |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Heating            | Wh     | energy       | 0.0                       |
| Home Away Mode                                                                |        |              | off                       |
| Home EEBUS                                                                    |        |              | off                       |
| Home Manual Cooling                                                           |        |              | off                       |
| Home Domestic Hot Water 0 Boost                                               |        |              | off                       |
| Home Zone 1 (Circuit 0) Ventilation Boost                                     |        |              | off                       |
| Home Domestic Hot Water 0                                                     |        |              | Time Controlled           |

## Climate Entities

Home Assistant's built-in climate modes differ from Vaillant's.
The following table shows the mapping for zones:

=== "VRC720 Controller"
        
    | Home Assistant Mode                                                              | Home Assistant Preset                      | Vaillant Mode        |
    |----------------------------------------------------------------------------------|--------------------------------------------|----------------------|
    | :material-power: Off                                                             | :material-circle-small: No Preset          | Off                  |
    | :material-thermostat-auto: Auto                                                  | :material-circle-small: No Preset          | Time Controlled Mode |
    | :material-thermostat-auto: Auto                                                  | :material-leaf: Eco Preset                 | Eco mode             |
    | :material-sun-snowflake-variant: Heat / Cool                                     | :material-circle-small: No Preset          | Manual Mode          |
    | :material-thermostat-auto: Auto<br/>:material-sun-snowflake-variant: Heat / Cool | :material-account-arrow-right: Away Preset | Away Mode            |
    | :material-thermostat-auto: Auto<br/>:material-sun-snowflake-variant: Heat / Cool | :material-rocket-launch: Boost Preset      | Quick Veto Mode      |
    | :material-thermostat-auto: Auto<br/>:material-sun-snowflake-variant: Heat / Cool | :material-bed: Sleep Preset                | Off                  |

=== "VRC700 Controller"
        
    | Home Assistant Mode             | Home Assistant Preset             | Vaillant Mode |
    |---------------------------------|-----------------------------------|---------------|
    | :material-power: Off            | :material-circle-small: No Preset | Off           |
    | :material-thermostat-auto: Auto | :material-circle-small: No Preset | Auto Mode     |
    | :material-thermostat-auto: Auto | :material-home: Home Preset       | Day Mode      |
    | :material-thermostat-auto: Auto | :material-leaf: Eco Preset        | Night Mode    |

### Ambisense Room Thermostats

There are separate climate entities for Ambisense room thermostats (only supported on VRC700 controllers):

| Home Assistant Mode                                                               | Home Assistant Preset                 | Vaillant Mode   |
|-----------------------------------------------------------------------------------|---------------------------------------|-----------------|
| :material-power: Off                                                              | :material-circle-small: No Preset     | Off             |
| :material-thermostat-auto: Auto                                                   | :material-circle-small: No Preset     | Auto Mode       |
| :material-sun-snowflake-variant: Heat / Cool                                      | :material-circle-small: No Preset     | Manual Mode     |
| :material-thermostat-auto: Auto<br />:material-sun-snowflake-variant: Heat / Cool | :material-rocket-launch: Boost Preset | Quick Veto Mode |

## Calendar Entities

<video style="float: right; width: 40%; margin: 0 0 15px 15px; min-width: 200px;" autoplay muted loop playsinline style="max-width: 600px; width: 100%; margin: 0 auto;">
    <source src="/mypyllant-component/assets/calendar.mp4" type="video/mp4">
</video>

Each zone and water heater has a calendar for changing the heating schedule. Water heaters also have a calendar for 
the circulation pump.

In each calendar, you can:

* Create new time slots (set a target temperature as the event summary)
* Update existing time slots by changing start time, end time, weekdays, or the target temperature in the event summary
* Delete time slots on a specific weekday

!!! note

    Make sure to select weekly repetition whenever you create, update, or delete events.

    Individual events can't be edited, only the whole weekly schedule.

## Extra State Attributes

Some entities come with extra state attributes for debugging and advanced usage. Your attributes may be different,
depending on your devices.

### Home Sensor

```yaml
migration_finished_at: redacted
online_state: ONLINE
cooling_start_temperature: 15
continuous_heating_start_setpoint: -26
alternative_point: -21
heating_circuit_bivalence_point: -10
dhw_bivalence_point: -7
automatic_cooling_on_off: false
adaptive_heating_curve: true
dhw_maximum_loading_time: 60
dhw_hysteresis: 5
dhw_flow_setpoint_offset: 25
continuous_heating_room_setpoint: 20
hybrid_control_strategy: BIVALENCE_POINT
max_flow_setpoint_hp_error: 25
dhw_maximum_temperature: 80
maximum_preheating_time: 0
paralell_tank_loading_allowed: false
outdoor_temperature: 20.097656
outdoor_temperature_average24h: 20.464844
system_water_pressure: 1.7
energy_manager_state: STANDBY
system_off: false
controller_type: VRC720
system_scheme: 8
backup_heater_type: CONDENSING
backup_heater_allowed_for: DHW_AND_HEATING
temporary_allow_backup_heater: DISABLED
module_configuration_v_r71: 3
energy_provide_power_cut_behavior: DISABLE_HEATPUMP_AND_BACKUP_HEATER
smart_photovoltaic_buffer_offset: 10
external_energy_management_activation: false
energy_management: 
  energy_manager:
    available: false
    compatible: false
  energy_management_status:
    thermal_storage:
      domestic_hot_water:
        available: false
        selected: false
      heating_buffer_cylinder:
        available: false
        selected: true
eebus: 
  ski: redacted
  brand: Vaillant
  type: Gateway
  model: VR921
  spine_enabled: false
  spine_enabled_status: DETERMINED
  pine_capable: true
```

### Control Error Binary Sensor

```yaml
diagnostic_trouble_codes:
  - serial_number:
    article_number: '0020260962'
    codes: [ ]
  - serial_number:
    article_number: '0010021118'
    codes: [ ]
  - serial_number:
    article_number: '0010023609'
    codes: [ ]
  - serial_number:
    article_number: '0020260914'
    codes: [ ]
```

### Climate Entity

```yaml
hvac_modes: off, heat_cool, auto
min_temp: 7
max_temp: 35
preset_modes: boost, none, away, sleep
current_temperature: 21.5
temperature: 0
current_humidity: 53
preset_mode: none
time_program_heating:
  extra_fields: { }
  monday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  tuesday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  wednesday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  thursday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  friday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  saturday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  sunday:
    - extra_fields: { }
      start_time: 420
      end_time: 1290
      setpoint: 21
  meta_info:
    min_slots_per_day: 0
    max_slots_per_day: 12
    setpoint_required_per_slot: true

quick_veto_start_date_time: null
quick_veto_end_date_time: null
```

### Circuit State Sensor

```yaml
room_temperature_control_mode: THERMOSTAT_FUNCTION
cooling_flow_temperature_minimum_setpoint: 20
heating_circuit_type: DIRECT_HEATING_CIRCUIT
heating_circuit_flow_setpoint: 0
heating_circuit_flow_setpoint_excess_offset: 0
heat_demand_limited_by_outside_temperature: 19
```

### Domestic Hot Water Entity

```yaml
min_temp: 35
max_temp: 70
operation_list: Manual, Time Controlled, Off, Cylinder Boost
current_temperature: 44
temperature: 50
target_temp_high: null
target_temp_low: null
operation_mode: Time Controlled
time_program_dhw:
  extra_fields: { }
  monday:
    - extra_fields: { }
      start_time: 330
      end_time: 1260
  tuesday:
    - extra_fields: { }
      start_time: 330
      end_time: 1260
  wednesday:
    - extra_fields: { }
      start_time: 330
      end_time: 1260
  thursday:
    - extra_fields: { }
      start_time: 330
      end_time: 1260
  friday:
    - extra_fields: { }
      start_time: 330
      end_time: 1260
  saturday:
    - extra_fields: { }
      start_time: 450
      end_time: 1260
  sunday:
    - extra_fields: { }
      start_time: 450
      end_time: 1260
  meta_info:
    min_slots_per_day: 0
    max_slots_per_day: 3
    setpoint_required_per_slot: false

time_program_circulation_pump:
  extra_fields: { }
  monday: [ ]
  tuesday: [ ]
  wednesday: [ ]
  thursday: [ ]
  friday: [ ]
  saturday: [ ]
  sunday: [ ]
  meta_info:
    min_slots_per_day: 0
    max_slots_per_day: 3
    setpoint_required_per_slot: false
```
