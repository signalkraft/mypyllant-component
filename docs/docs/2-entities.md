---
hide:
  - navigation
---

# Entities

You can expect these entities, although names may vary based on your installed devices (in this example "aroTHERM plus" 
and "Hydraulic Station") or the naming of your heating zones (in this case "Zone 1"):

| Entity                                                          | Unit   | Class        | Sample                    |
|-----------------------------------------------------------------|--------|--------------|---------------------------|
| Outdoor Temperature                                             | °C     | temperature  | 16.7                      |
| System Water Pressure                                           | bar    | pressure     | 1.0                       |
| My Home VR 921                                                  |        |              | 0357.40.30                |
| Desired Temperature in Zone 1                                   | °C     | temperature  | 5.0                       |
| Current Temperature in Zone 1                                   | °C     | temperature  | 20.9                      |
| Humidity in Zone 1                                              | %      | humidity     | 60.0                      |
| Heating Operating Mode in Zone 1                                |        |              | Off                       |
| Heating State in Zone 1                                         |        |              | Idle                      |
| Current Special Function in Zone 1                              |        |              | None                      |
| State in Circuit 0                                              |        |              | STANDBY                   |
| Current Flow Temperature in Circuit 0                           | °C     | temperature  | 35.5                      |
| Heating Curve in Circuit 0                                      |        |              | 0.68                      |
| Tank Temperature Domestic Hot Water 255                         | °C     | temperature  | 48.5                      |
| Setpoint Domestic Hot Water 255                                 | °C     | temperature  | 50.0                      |
| Operation Mode Domestic Hot Water 255                           |        |              | Time Controlled           |
| Current Special Function Domestic Hot Water 255                 |        |              | Regular                   |
| Heating Energy Efficiency                                       |        |              | 3.0                       |
| aroTHERM plus Consumed Electrical Energy Domestic Hot Water     | Wh     | energy       | 2000.0                    |
| aroTHERM plus Consumed Electrical Energy Heating                | Wh     | energy       | 1000.0                    |
| aroTHERM plus Earned Environment Energy Domestic Hot Water      | Wh     | energy       | 6000.0                    |
| aroTHERM plus Earned Environment Energy Heating                 | Wh     | energy       | 0.0                       |
| aroTHERM plus Heat Generated Heating                            | Wh     | energy       | 1000.0                    |
| aroTHERM plus Heat Generated Domestic Hot Water                 | Wh     | energy       | 8000.0                    |
| hydraulic station Consumed Electrical Energy Domestic Hot Water | Wh     | energy       | 0.0                       |
| hydraulic station Consumed Electrical Energy Heating            | Wh     | energy       | 0.0                       |
| Domestic Hot Water 0                                            |        |              | Time Controlled           |
| Zone 1                                                          |        |              | off                       |
| Trouble Codes on aroTHERM plus                                  |        | problem      | off                       |
| Online Status aroTHERM plus                                     |        | connectivity | on                        |
| Firmware Update Required My Home VR 921                         |        | update       | off                       |
| Firmware Update Enabled My Home VR 921                          |        |              | on                        |
| Cooling Allowed in Circuit 0                                    |        |              | off                       |

## Extra State Attributes

Some entities come with extra state attributes for debugging and advanced usage. Your attributes may be different, depending on your devices.

### Home Sensor

```yaml
continuous_heating_start_setpoint: -26
alternative_point: -21
heating_circuit_bivalence_point: 0
dhw_bivalence_point: -7
automatic_cooling_on_off: false
adaptive_heating_curve: true
dhw_maximum_loading_time: 60
dhw_hysteresis: 3
dhw_flow_setpoint_offset: 25
continuous_heating_room_setpoint: 20
hybrid_control_strategy: BIVALENCE_POINT
max_flow_setpoint_hp_error: 25
dhw_maximum_temperature: 80
maximum_preheating_time: 0
paralell_tank_loading_allowed: false
outdoor_temperature: 8.019531
system_water_pressure: 1.6
outdoor_temperature_average24h: 9.707031
controller_type: VRC720
system_scheme: 8
backup_heater_type: CONDENSING
backup_heater_allowed_for: DHW_AND_HEATING
module_configuration_v_r71: 3
energy_provide_power_cut_behavior: DISABLE_HEATPUMP_AND_BACKUP_HEATER
```

### Control Error Binary Sensor

```yaml
diagnostic_trouble_codes: 
- serial_number: 
  article_number: '0020260962'
  codes: []
- serial_number: 
  article_number: '0010021118'
  codes: []
- serial_number: 
  article_number: '0010023609'
  codes: []
- serial_number: 
  article_number: '0020260914'
  codes: []
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
  extra_fields: {}
  monday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  tuesday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  wednesday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  thursday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  friday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  saturday:
    - extra_fields: {}
      start_time: 420
      end_time: 1290
      setpoint: 21
  sunday:
    - extra_fields: {}
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
  extra_fields: {}
  monday:
    - extra_fields: {}
      start_time: 330
      end_time: 1260
  tuesday:
    - extra_fields: {}
      start_time: 330
      end_time: 1260
  wednesday:
    - extra_fields: {}
      start_time: 330
      end_time: 1260
  thursday:
    - extra_fields: {}
      start_time: 330
      end_time: 1260
  friday:
    - extra_fields: {}
      start_time: 330
      end_time: 1260
  saturday:
    - extra_fields: {}
      start_time: 450
      end_time: 1260
  sunday:
    - extra_fields: {}
      start_time: 450
      end_time: 1260
  meta_info:
    min_slots_per_day: 0
    max_slots_per_day: 3
    setpoint_required_per_slot: false

time_program_circulation_pump: 
  extra_fields: {}
  monday: []
  tuesday: []
  wednesday: []
  thursday: []
  friday: []
  saturday: []
  sunday: []
  meta_info:
    min_slots_per_day: 0
    max_slots_per_day: 3
    setpoint_required_per_slot: false
```
