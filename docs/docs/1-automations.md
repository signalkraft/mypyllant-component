---
hide:
  - navigation
---

# Automations

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

1. You can customize the frequency and weekday here, see [Time condition documentation](https://www.home-assistant.io/docs/scripts/conditions/#time-condition)
2. Here you can set the target temperature for legionella protection
3. This is the duration. Make sure it covers the time period where your water heater is turned on
4. This should be your regular water temperature

## Setting a Time Program

Call the `mypyllant.set_zone_time_program` (for climate) `mypyllant.set_dhw_time_program` (for water heaters) 
with a `program_type` (only on climate) and a `time_program`.

=== "Climate"

    ```yaml
    service: mypyllant.set_zone_time_program
    data:
      program_type: heating
      time_program:
        monday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        tuesday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        wednesday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        thursday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        friday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        saturday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        sunday:
          - start_time: 420
            end_time: 1290
            setpoint: 20
        type: heating
    target:
      entity_id: climate.zone_0
    ```

=== "Water Heater"

    ```yaml
    service: mypyllant.set_dhw_time_program
    data:
      time_program:
        monday:
          - start_time: 420
            end_time: 1290
        tuesday:
          - start_time: 420
            end_time: 1290
        wednesday:
          - start_time: 420
            end_time: 1290
        thursday:
          - start_time: 420
            end_time: 1290
        friday:
          - start_time: 420
            end_time: 1290
        saturday:
          - start_time: 420
            end_time: 1290
        sunday:
          - start_time: 420
            end_time: 1290
        type: heating
    target:
      entity_id: water_heater.domestic_hot_water_0
    ```

=== "Circulation Pump"

    ```yaml
    service: mypyllant.set_dhw_circulation_time_program
    data:
      time_program:
        monday:
          - start_time: 420
            end_time: 1290
        tuesday:
          - start_time: 420
            end_time: 1290
        wednesday:
          - start_time: 420
            end_time: 1290
        thursday:
          - start_time: 420
            end_time: 1290
        friday:
          - start_time: 420
            end_time: 1290
        saturday:
          - start_time: 420
            end_time: 1290
        sunday:
          - start_time: 420
            end_time: 1290
        type: heating
    target:
      entity_id: water_heater.domestic_hot_water_0
    ```

[^1]: Contributed by CommanderROR in the [Home Assistant Community](https://community.home-assistant.io/t/myvaillant-integration/542610/70)