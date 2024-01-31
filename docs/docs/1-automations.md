---
description: Useful Home Assistant automations with mypyllant-component
hide:
  - navigation
---

# Automations & Cards

## Legionella Protection[^1]

With the Home Assistant component, more flexible legionella protection is possible. You can tweak the time condition
or the target temperature(s).

```yaml
alias: Legionella Protection
description: ""
trigger:
  - platform: time
    at: "10:00:00"
condition:
  - condition: time
    weekday:
      - sun  # (1)
action:
  - service: water_heater.set_temperature
    data:
      temperature: 75 # (2)
    target:
      entity_id: water_heater.domestic_hot_water_0
  - delay:
      hours: 8 # (3)
      minutes: 0
      seconds: 0
      milliseconds: 0
  - service: water_heater.set_temperature
    data:
      temperature: 50 # (4)
    target:
      entity_id: water_heater.domestic_hot_water_0
mode: single
```

1. You can customize the frequency and weekday here,
   see [Time condition documentation](https://www.home-assistant.io/docs/scripts/conditions/#time-condition)
2. Here you can set the target temperature for legionella protection
3. This is the duration. Make sure it covers the time period where your water heater is turned on
4. This should be your regular water temperature

## Turning off Water Heater with Climate Away Mode

With these two automations, your water heater turns on and off with the away mode of your climate entity.

```yaml
alias: Water heater off during Zone 1 away mode
description: ""
trigger:
  - platform: state
    entity_id:
      - climate.home_zone_1_circuit_0_climate # (1)
    attribute: preset_mode
    to: away
condition: [ ]
action:
  - service: water_heater.set_operation_mode
    target:
      entity_id:
        - water_heater.home_domestic_hot_water_0 # (2)
    data:
      operation_mode: 'OFF'
mode: single
```

1. Pick your climate entity
2. Pick your water heater entity

```yaml
alias: myVAILLANT DHW on after ending away mode
description: ""
trigger:
  - platform: state
    entity_id:
      - climate.home_zone_1_circuit_0_climate # (1)
    attribute: preset_mode
    from: away
condition: [ ]
action:
  - service: water_heater.set_operation_mode
    target:
      entity_id:
        - water_heater.home_domestic_hot_water_0 # (2)
    data:
      operation_mode: TIME_CONTROLLED
mode: single
```

1. Pick your climate entity
2. Pick your water heater entity

## Control Heating Schedule based on Solar Power

This automation delays heating until after sunrise on sunny days, to make the most of solar power.
You could also use your water heater schedule, to boost tank temperature at the end of the day
when solar power is still available.

```yaml
alias: myVAILLANT Delay Heating on Sunny Days
description: ""
trigger:
  - platform: calendar
    event: start
    offset: "0:30:0"
    entity_id: calendar.home_zone_1_circuit_0_heating_schedule # (1)
condition:
  - condition: numeric_state
    entity_id: sensor.openweathermap_forecast_cloud_coverage # (2)
    below: 50
  - condition: sun
    before: sunrise
action:
  - service: mypyllant.set_holiday
    target:
      entity_id: climate.home_zone_1_circuit_0_climate # (3)
    data:
      end: "{{ (as_timestamp(states.sensor.sun_next_rising.state) + 1.5 * 3600) | timestamp_local }}" # (4)
mode: single
```

1. Pick your calendar entity. The offset makes sure that a little bit of heating still happens at the scheduled start
2. Uses OpenWeatherMap to determine forecasted cloud coverage, only triggers if cloud coverage is below 50%
3. Pick your climate entity
4. Delays heating until 1,5h after sunrise

## Climate Control Cards with Away Mode Datepickers

This is a sample card configuration with climate & water heater controls, as well as a conditional switch
for away mode that shows date pickers when away mode is enabled. You probably need to replace `home` and
`zone_1` with your entity names.

![img.png](assets/climate-cards.png)

You need the [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) addon.

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-chips-card
    chips:
      - type: entity
        entity: binary_sensor.home_online_status
      - type: entity
        entity: sensor.home_zone_1_circuit_0_heating_state
        icon: mdi:air-purifier
      - type: entity
        entity: sensor.home_zone_1_circuit_0_current_temperature
      - type: entity
        entity: sensor.home_system_water_pressure
  - type: custom:mushroom-climate-card
    entity: climate.home_zone_1_circuit_0_climate
    fill_container: false
    hvac_modes:
      - auto
      - heat_cool
      - 'off'
    show_temperature_control: false
    collapsible_controls: false
    icon: mdi:heat-pump
    tap_action:
      action: more-info
    secondary_info: state
  - type: custom:mushroom-entity-card
    entity: switch.home_holiday_duration_remaining
    tap_action:
      action: toggle
    fill_container: false
    layout: horizontal
  - type: conditional
    conditions:
      - condition: state
        entity: switch.home_holiday_duration_remaining
        state: 'on'
    card:
      type: entities
      entities:
        - entity: datetime.home_away_mode_start_date
        - entity: datetime.home_away_mode_end_date
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: water_heater.home_domestic_hot_water_0
        name: Hot Water
        icon: mdi:thermometer-water
      - type: custom:mushroom-entity-card
        entity: switch.home_domestic_hot_water_0_boost
        name: Hot Water Boost
        icon: mdi:thermometer-chevron-up
        tap_action:
          action: toggle
```

## Customizing Schedules in the Calendar

<video autoplay muted loop playsinline style="max-width: 600px; width: 100%; margin: 0 auto;">
    <source src="/mypyllant-component/assets/calendar.mp4" type="video/mp4">
</video>

Time programs can be updated from the Home Assistant calendar. You can:

* Create new time slots (make sure to select weekly repetition, and set a target temperature as the event summary)
* Update existing time slots by changing start time, end time, weekdays, or the target temperature in the event summary
* Delete time slots on a specific weekday

[^1]: Contributed by CommanderROR in
the [Home Assistant Community](https://community.home-assistant.io/t/myvaillant-integration/542610/70)