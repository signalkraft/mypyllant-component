---
description: Home Assistant services to control your myVAILLANT devices
hide:
  - navigation
  - toc
---

# Services

There are custom services to control holiday mode and quick veto temperatures for each climate zone.
Search for "myvaillant" in Developer Tools > Services in your Home Assistant instance to get the full list plus an interactive UI.

![Services Screenshot](assets/services-screenshot.png)

[![Open your Home Assistant instance and show your service developer tools with a specific service selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_holiday)

## Setting a Time Program

The following services can be used to set time programs:

* `mypyllant.set_zone_time_program` for climate zones (requires an additional `program_type`)
* `mypyllant.set_zone_time_program` for climate zones
* `mypyllant.set_dhw_circulation_time_program` for circulation pumps on water heaters

You can look up your current time programs in the [developer states view](https://my.home-assistant.io/redirect/developer_states/)
under attributes for your zones and water heater.

Times in the time program are given in minutes since midnight in UTC.

!!! note "Disabling a time window"

    You can delete all time windows on a day by sending an empty list, for example `monday: []`.

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