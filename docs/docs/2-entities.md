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
| Home Trouble Codes                                                            |        | problem      | off                       |
| Home Online Status                                                            |        | connectivity | on                        |
| Home Firmware Update Required                                                 |        | update       | off                       |
| Home Firmware Update Enabled                                                  |        |              | on                        |
| Home EEBUS Enabled                                                            |        |              | on                        |
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
| Home Manual Cooling Duration                                                  | d      |              | 0                         |
| Home Zone 1 (Circuit 0) Quick Veto Duration                                   | h      |              | 2                         |
| Home Circuit 0 Heating Curve                                                  |        |              | 1.2733452                 |
| Home Circuit 0 Heat Demand Limited by Outside Temperature                     | °C     |              | 18.0                      |
| Home Circuit 0 Min Flow Temperature Setpoint                                  | °C     |              | 32.0                      |
| Vaillant API Request Count                                                    |        |              | 51                        |
| Home Outdoor Temperature                                                      | °C     | temperature  | 17.3                      |
| Home System Water Pressure                                                    | bar    | pressure     | 1.5                       |
| Home Firmware Version                                                         |        |              | 0357.40.35                |
| Home Zone 1 (Circuit 0) Desired Temperature                                   | °C     | temperature  | 0.0                       |
| Home Zone 1 (Circuit 0) Desired Heating Temperature                           | °C     | temperature  | 0.0                       |
| Home Zone 1 (Circuit 0) Desired Cooling Temperature                           | °C     | temperature  | 25.0                      |
| Home Zone 1 (Circuit 0) Current Temperature                                   | °C     | temperature  | 21.5                      |
| Home Zone 1 (Circuit 0) Humidity                                              | %      | humidity     | 62.0                      |
| Home Zone 1 (Circuit 0) Heating Operating Mode                                |        |              | Time Controlled           |
| Home Zone 1 (Circuit 0) Heating State                                         |        |              | Idle                      |
| Home Zone 1 (Circuit 0) Current Special Function                              |        |              | Quick Veto                |
| Home Circuit 0 State                                                          |        |              | STANDBY                   |
| Home Circuit 0 Current Flow Temperature                                       | °C     | temperature  | 41.0                      |
| Home Circuit 0 Heating Curve                                                  |        |              | 1.27                      |
| Home Domestic Hot Water 0 Tank Temperature                                    | °C     | temperature  | 51.5                      |
| Home Domestic Hot Water 0 Setpoint                                            | °C     | temperature  | 52.0                      |
| Home Domestic Hot Water 0 Operation Mode                                      |        |              | Time Controlled           |
| Home Domestic Hot Water 0 Current Special Function                            |        |              | Regular                   |
| Home Heating Energy Efficiency                                                |        |              | 4.9                       |
| Home Device 0 aroTHERM plus Heating Energy Efficiency                         |        |              | 4.9                       |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Cooling                | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Domestic Hot Water     | Wh     | energy       | 3000.0                    |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Heating                | Wh     | energy       | 4000.0                    |
| Home Device 0 aroTHERM plus Earned Environment Energy Cooling                 | Wh     | energy       | 0.0                       |
| Home Device 0 aroTHERM plus Earned Environment Energy Domestic Hot Water      | Wh     | energy       | 9000.0                    |
| Home Device 0 aroTHERM plus Earned Environment Energy Heating                 | Wh     | energy       | 18000.0                   |
| Home Device 0 aroTHERM plus Heat Generated Heating                            | Wh     | energy       | 22000.0                   |
| Home Device 0 aroTHERM plus Heat Generated Domestic Hot Water                 | Wh     | energy       | 12000.0                   |
| Home Device 0 aroTHERM plus Heat Generated Cooling                            | Wh     | energy       | 0.0                       |
| Home Device 1 Hydraulic Station Heating Energy Efficiency                     |        |              | unknown                   |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Domestic Hot Water | Wh     | energy       | 0.0                       |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Heating            | Wh     | energy       | 0.0                       |
| Home Away Mode                                                                |        |              | off                       |
| Home EEBUS                                                                    |        |              | on                        |
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

## Energy Statistics

In addition to the [energy sensors listed above](#sample-entities) (which show *today's running total* for each
device and operation mode), the integration imports the myVAILLANT **hourly** energy data into
Home Assistant's long-term statistics. This is what powers correct per-hour attribution in the
**Energy Dashboard**. Each hour's heat-pump consumption is recorded against the hour it
actually happened, not the time it was retrieved.

These statistics appear under external IDs of the form
`mypyllant:mypyllant_<system>_<device>_<operation>_<index>` (Developer Tools → Statistics), one
per energy sensor (e.g. *Consumed Electrical Energy Domestic Hot Water*, *... Heating*).

### How it works

* On each refresh, the daily-data coordinator fetches **two days** of hourly buckets
  (yesterday + today) from the myVAILLANT API and writes them as external statistics.
* `sum` is **cumulative and monotonically increasing** (it carries the previous day's running
  total forward), so the Energy Dashboard never shows a negative spike at midnight.
* `state` and `last_reset` reset at the start of **each** day, mirroring how other energy
  integrations (e.g. `octopus_energy`) model day-cumulative statistics.

### Why two days are fetched

The myVAILLANT API only returns a value for **completed** hours: the hour currently in
progress comes back as `null`. That includes the **final hour of the day** (23:00–00:00): at
23:55 it is still in progress, so it cannot be captured before midnight. Because the coordinator
re-fetches *yesterday* as well as today, a refresh shortly **after** midnight backfills that
final hour once it has finalised. Re-writing yesterday is idempotent (identical `sum` values),
so the only new row added is the previously-missing hour.

### Keeping the data up to date

!!! danger "important"

    To avoid hitting the myVAILLANT API quota, the **daily energy data is *not* refreshed
    automatically**: it is only fetched once when the integration loads. You therefore need to
    trigger a refresh yourself to keep the hourly statistics current. There are two recommended
    approaches depending on whether you have hourly electricity metering in Home Assistant.

A refresh is triggered by calling `homeassistant.update_entity` on **any** of the integration's
energy / efficiency sensors (e.g. `sensor.home_device_0_arotherm_plus_heating_energy_efficiency`).
You can also set the **"Seconds between energy data updates"** option (`update_interval_daily`,
left empty by default) to poll on a fixed interval, but an automation gives you more control over
timing and quota.

Note that the myVAILLANT API finalises a completed hour a few minutes after it ends, so trigger
the refresh a little **past** the hour (`:15` works well) rather than exactly on the hour.

#### Option A: hourly electricity metering (recommended)

If Home Assistant knows your grid consumption (e.g. from a smart-meter / DNO integration), only
poll myVAILLANT when the heat pump has actually drawn power in the previous hour. This keeps API
usage low while capturing every active hour within ~1 hour.

First create a **helper** that reports your grid consumption over a rolling ~hour, using the
built-in [`statistics`](https://www.home-assistant.io/integrations/statistics/) platform. Point
it at an accumulative (monotonically increasing) consumption sensor in kWh:

```yaml
# configuration.yaml
sensor:
  - platform: statistics
    name: "Grid consumption rolling hour"
    unique_id: grid_consumption_rolling_hour
    entity_id: sensor.electricity_meter_accumulative_consumption  # your smart-meter kWh total
    state_characteristic: change      # net change over the buffered window
    max_age:
      minutes: 55
    sampling_size: 250
```

!!! note

    If your consumption sensor resets at midnight, `change` may briefly read negative around the
    reset; the `above: 1` condition below simply won't fire then, which is harmless. The 00:30
    snapshot covers that boundary.

Then add an automation that refreshes at `:15` when the previous hour's consumption exceeded a
threshold (1 kWh works well: high enough to ignore base load, low enough to catch any
real heat-pump cycle), plus an **unconditional 00:30 snapshot** that backfills the previous day
in full:

```yaml
# automations.yaml
- id: mypyllant_energy_refresh
  alias: myVAILLANT - Refresh energy data
  description: >
    Refresh hourly energy at :15 when the previous hour's grid usage exceeded 1 kWh (so we
    only poll when the heat pump likely ran), plus an unconditional 00:30 daily snapshot that
    backfills the previous day's final hour.
  triggers:
    - trigger: time_pattern
      minutes: "15"
      id: hourly
    - trigger: time
      at: "00:30:00"
      id: snapshot
  conditions:
    - condition: or
      conditions:
        - condition: numeric_state
          entity_id: sensor.grid_consumption_rolling_hour
          above: 1
        - condition: trigger
          id: snapshot
  actions:
    - action: homeassistant.update_entity
      target:
        entity_id: sensor.home_device_0_arotherm_plus_heating_energy_efficiency
  mode: single
```

Because the daily snapshot reprocesses the whole previous day, any hour missed intraday (for
example a short cycle that didn't cross the 1 kWh threshold) is recovered automatically by the
next morning. Daily totals are always correct.

#### Option B: no hourly metering

If you don't have an hourly grid-consumption sensor to gate on, simply refresh **once per day at
00:30**. Thanks to the two-day fetch, this pulls the *entire* previous day (now complete,
including its final hour) plus the current day so far. You get accurate per-hour data one day in
arrears:

```yaml
# automations.yaml
- id: mypyllant_energy_daily_refresh
  alias: myVAILLANT - Daily energy refresh
  description: Pull the full previous day's hourly energy at 00:30 (data lands one day in arrears).
  triggers:
    - trigger: time
      at: "00:30:00"
  actions:
    - action: homeassistant.update_entity
      target:
        entity_id: sensor.home_device_0_arotherm_plus_heating_energy_efficiency
  mode: single
```

### Visualising with Plotly Graph

The long-term statistics can be displayed as hourly bar charts using the
[Plotly Graph Card](https://github.com/dbuezas/lovelace-plotly-graph-card).

!!! note "Why not ApexCharts?"

    The popular ApexCharts card requires a standard entity ID for every
    series. It cannot query external statistics directly, which means you cannot mix a
    `mypyllant:` statistic (energy bars) with a normal temperature sensor in the same chart. Plotly
    Graph Card supports both in a single card via its `statistic:` option.

Because the statistics are external, each energy series must use `statistic: sum` with
`period: hour` and a `delta` filter to convert the cumulative sum into per-hour consumption
values. Find your statistic ID in **Developer Tools → Statistics** (filter by `mypyllant:`).

Temperature sensors (tank, zone, outdoor) are also recorded as long-term statistics by HA's
recorder. Using `statistic: mean` with `period: hour` on temperature series aligns them to the
same hourly bucket as the energy bars, which gives accurate correlation across 7- and 14-day
views.

**Example: Domestic Hot Water energy vs tank temperature**

```yaml
type: custom:plotly-graph
title: Hot Water ℃ vs Energy Usage
hours_to_show: 24
refresh_interval: auto
autorange_after_scroll: true # (7)
entities:
  - entity: sensor.home_domestic_hot_water_0_tank_temperature
    name: Tank Temperature
    statistic: mean # (1)
    period: hour
    line:
      color: "#e74c3c"
      width: 2
  - entity: mypyllant:mypyllant_<your_statistic_id>
    name: DHW Energy (Wh/h)
    unit_of_measurement: Wh # (5)
    statistic: sum # (2)
    period: hour
    type: bar
    yaxis: y2
    marker:
      color: rgba(52, 152, 219, 0.6)
    filters:
      - delta # (3)
      - map_y_numbers: Math.max(0, y) # (4)
layout:
  xaxis:
    rangeselector: # (8)
      y: 1.1
      buttons:
        - count: 1
          step: day
          label: 1 Day
        - count: 7
          step: day
          label: 7 Days
        - count: 14
          step: day
          label: 14 Days
  yaxis:
    title: Temperature (°C)
  yaxis2:
    title: Energy (Wh)
    overlaying: y
    side: right
    rangemode: tozero
    hoverformat: .0f # (6)
```

1. Reads the hourly mean from HA's recorder statistics, aligning the temperature line to the same hourly buckets as the energy bars.
2. Reads from the external long-term statistics written by this integration, not entity state history.
3. Converts the monotonically increasing `sum` into per-hour consumption values.
4. Suppresses the rare small negative value that can appear at day boundaries while the baseline is being established.
5. Required for the correct unit in the hover tooltip — external statistics don't expose their unit automatically to the card.
6. Displays whole-number Wh values in the tooltip.
7. Keeps axes scaled correctly when switching between time ranges.
8. Adds 1 Day / 7 Days / 14 Days quick-select buttons above the chart.
