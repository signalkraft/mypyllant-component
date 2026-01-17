---
title: Getting Started
description: Home Assistant component that interfaces with the myVAILLANT API (and branded versions of it, such as the MiGo Link app from Saunier Duval & Bulex).
hide:
  - navigation
---

[![myPyllant](assets/logo.png){ align=right width="25%" }]()

# Getting Started

[![GitHub Release](https://img.shields.io/github/release/signalkraft/mypyllant-component.svg)](https://github.com/signalkraft/mypyllant-component/releases)
[![License](https://img.shields.io/github/license/signalkraft/mypyllant-component.svg)](https://github.com/signalkraft/mypyllant-component/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/signalkraft/mypyllant-component/build-test.yaml)](https://github.com/signalkraft/mypyllant-component/actions)

Home Assistant component that interfaces with the myVAILLANT API
(and branded versions of it, such as the MiGo Link app from Saunier Duval & Bulex).
Uses the [myPyllant Python library](https://github.com/signalkraft/mypyllant).

## Installation

!!! note

    1. The developers are not affiliated with Vaillant, we take no responsibility for anything that happens to your devices because of this library
    1. This integration is not compatible with systems that use sensoAPP and multiMATIC

=== "HACS"

    1. [Install the Home Assistant Community Store (HACS)](https://hacs.xyz/docs/setup/download)
    2. Search for myVAILLANT in HACS :material-arrow-right: Integrations and download it
    3. Restart Home Assistant
    4. [Add myVaillant integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mypyllant), or go to
       Settings :material-arrow-right: Devices & services :material-arrow-right: Add Integration
    5. Sign in with the email & password you used in the myVAILLANT app (or MiGo app for Saunier Duval)

    Having problems? [Open an issue](https://github.com/signalkraft/mypyllant-component/issues/new/choose).

=== "Manual"
    
    1. Download [the latest release](https://github.com/signalkraft/mypyllant-component/releases)
    2. Extract the `custom_components` folder to your Home Assistant's config folder, the resulting folder structure should
       be `config/custom_components/mypyllant`
    3. Restart Home Assistant
    4. [Add myVaillant integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mypyllant), or go to
       Settings :material-arrow-right: Devices & services :material-arrow-right: Add Integration
    5. Sign in with the email & password you used in the myVAILLANT app (or MiGo app for Saunier Duval)

    Having problems? [Open an issue](https://github.com/signalkraft/mypyllant-component/issues/new/choose).


## Features

<div class="grid cards" markdown>

*    :material-sun-snowflake-variant:{ .lg .middle } Climate Controls

     ---

     Supports climate & hot water controls, as well as ventilation and circulation pumps

     [:material-arrow-right: Read more](2-entities.md#sample-entities)

*    :material-thermostat-auto:{ .lg .middle } Set Modes & Temperatures

     ---

     Control operating modes, target temperature, and presets such as holiday more or quick veto

     [:material-arrow-right: Read more](2-entities.md#climate-entities)

*    :material-calendar-sync:{ .lg .middle } Change Schedules

     ---

     Set the schedule for climate zones, water heaters, and circulation pumps
     with [a custom service](https://signalkraft.com/mypyllant-component/2-services/#setting-a-time-program) or [in the Home Assistant calendar](2-entities.md#calendar-entities)

     [:material-arrow-right: Read more](2-entities.md#calendar-entities)

*    :material-chart-line:{ .lg .middle } Track Data over Time

     ---

     Track sensor information of devices, such as temperature, humidity, operating mode, energy usage, or energy efficiency

    [:material-arrow-right: Read more](2-entities.md#sample-entities)

*    :material-hammer-screwdriver:{ .lg .middle } Diagnostic Data

     ---

     See diagnostic information, such as flow temperature, firmware versions, or water pressure.
     Even values that are not available in the app, such as the current heating curve.

     [:material-arrow-right: Read more](2-entities.md#extra-state-attributes)

*    :material-home-automation:{ .lg .middle } Services & Automations

     ---

     Custom services to set holiday mode or quick veto temperature overrides, and their duration

     [:material-arrow-right: Read more](2-services.md)

</div>

![Default Dashboard Screenshot](assets/default-dashboard.png)

## Tested Setups

* Vaillant aroTHERM plus heatpump + sensoCOMFORT VRC 720 + sensoNET VR 921
* Vaillant ECOTEC PLUS boiler + VR940F + sensoCOMFORT
* Vaillant ECOTEC PLUS boiler + VRT380f + sensoNET
* Vaillant ECOTEC PLUS VCW20/1 boiler + sensoCOMFORT VRC 720 + sensoNET VR 921
* Vaillant ECOTEC PLUS 296/5-5 (R6) + sensoCOMFORT VRC 720/2 + VR 70 (2 circuits) + sensoNET VR 921
* Vaillant ecoVIT + VIH R/6 uniSTORE + VR920
* Saunier Duval DUOMAX F30 90 + MISET Radio + MiLink V3
* Bulex Thema Condens F30/35 + Red 5 + MiPro Sense + MiLink v3


## Options

After setting up the integration, you can configure it further in Settings :material-arrow-right: Devices & Services :material-arrow-right: myVAILLANT :material-arrow-right: Configure.


!!! warning

    The integration fetches limited data by default, to avoid running into quota errors, or generating unnecessary
    errors (when trying to fetch data that' not available for your system).

    If you have data that's available in the myVAILLANT app, but not the integration, you probably need to modify
    the integration options starting with `Fetch XYZ`.


### Seconds between updates

:   Wait interval between updating (most) sensors. The energy data and efficiency sensors are controlled by the next option.
    Setting this too low can cause "quota exceeded" errors.

    You should restart Home Assistant after changing this setting.
    
    :material-cog: Default is 1800 seconds.

### Seconds between energy data updates

:   Wait interval between updating sensors with hourly data. Default is off, because querying for energy data can get
    you blocked by Vaillant quite easily ("quota exceeded" errors).

    Most users seem to be OK with 7200s (2 hours) or more.

    You can also schedule your own updates with an automation, for example once a day just before midnight:
    
    ```yaml
    description: "Update myVAILLANT energy data at midnight"
    mode: single
    triggers:
      - trigger: time
        at: "23:59:00"
    conditions: []
    actions:
        - action: homeassistant.update_entity
          metadata: {}
          data:
            entity_id:
              - sensor.home_heating_energy_efficiency
    ```

    You only need to update one of the energy entities, all of the other ones will automatically update as well.
    To reduce API queries and avoid getting blocked, you should disable energy entities in HA that you are not interested in.

    You should restart Home Assistant after changing this setting.
    
    :material-cog: Default is off.

### Delay in seconds before refreshing data after updates

:   How long to wait between making a request (i.e. setting target temperature) and refreshing data.
    The Vaillant API takes some time to return the updated values. Setting this too low will return the old values.
    
    :material-cog: Default is 5 seconds.

### Default duration in hours for quick veto

:   When setting the temperature with the climate controls, the integration uses the "quick veto" feature of the myVAILLANT
    app by default.
    
    With this option you can set for how long the temperature should stay set, before returning to the default value.

    :material-cog: Default is 3 hours.

### Default duration in days for away mode

:   When the away mode preset is activated, this duration is used to for the end date.

    :material-cog: Default is 365 days.

### Default temperature setpoint for away mode

:   When away mode is activated without a temperature (for example with the away mode switch), this value is set for all zones.

    :material-cog: Default is 10.0°C.

### Temperature controls overwrite time program instead of setting quick veto

:   When raising or lowering the desired temperature in the myVAILLANT app, it sets a quick veto mode for a limited time
    with that new temperature, if the zone is in time controlled mode. If you want to permanently change the desired
    temperature, you need to update the time schedule.

    By default, this integration has the same behavior. But when enabling this option, the Home Assistant climate controls
    instead overwrite the temperatures set in the time schedule with the new value.

    :material-cog: Default is off.

    !!! note
    
        If quick veto is active, the climate controls will always set the quick veto temperature.

### Fetch real-time statistics (not supported on every system)

:   Fetches real-time statistics from the system. This includes on/off cycles and operation time.
    If you see 404 errors in your logs after enabling this, your system doesn't support this data.
    It's best to turn it off again.

    :material-cog: Default is off.

### Fetch real-time power usage (not supported on every system)

:   Fetches real-time power usage of the system.
    If you see 404 errors in your logs after enabling this, your system doesn't support this data.
    It's best to turn it off again.

    :material-cog: Default is off.

### Fetch system connection status

:   Fetches connection status of the system (Connected / Offline).

    :material-cog: Default is off.

### Fetch diagnostic trouble codes

:   Fetches diagnostic trouble codes of the system, for each connected & supported device.

    :material-cog: Default is off.

### Fetch Ambisense Capability

:   Fetches information, whether the system has Ambisense capabilities.

    :material-cog: Default is off.

### Fetch Ambisense Room Thermostats (not supported on every system)

:   Fetches Ambisense room thermostat data.
    If you see 404 errors in your logs after enabling this, your system doesn't support this data.
    It's best to turn it off again.

    :material-cog: Default is off.

### Fetch EEBUS Data

:   Fetches information whether EEBUS is available or not.

    :material-cog: Default is off.

### Fetch Energy Management Data

:   Fetches energy management data from EEBUS.

    :material-cog: Default is off.

### Country

:   The country you registered your myVAILLANT account in. The list of options is limited to known supported countries.

### Brand

:   Brand of your HVAC equipment and app, pick Saunier Duval if you use the MiGo Link app.

## Supported Brands & Countries

!!! note "Missing a Country?"

    If a country is missing, please [open an issue](https://github.com/signalkraft/myPyllant/issues/new/choose)
    or [contribute a new country to the myPyllant library](3-contributing.md#supporting-new-countries).

- Vaillant
    - Albania
    - Austria
    - Belgium
    - Bulgaria
    - Croatia
    - Czechia
    - Denmark
    - Estonia
    - Finland
    - France
    - Georgia
    - Germany
    - Greece
    - Hungary
    - Italy
    - Latvia
    - Lithuania
    - Luxembourg
    - Netherlands
    - Norway
    - Poland
    - Portugal
    - Romania
    - Serbia
    - Slovakia
    - Slovenia
    - Spain
    - Sweden
    - Switzerland
    - Ukraine
    - United Kingdom
    - Uzbekistan
- Saunier Duval
    - Austria
    - Czechia
    - Finland
    - France
    - Greece
    - Hungary
    - Italy
    - Lithuania
    - Poland
    - Portugal
    - Romania
    - Slovakia
    - Spain
- Bulex
    - Does not support country selection, just leave the option empty

## Known Issues

### Lack of Test Data for Different Systems

Your HVAC system might differ from the ones in [Tested Setups](#tested-setups) above.
If you don't see any entities, or get an error during setup, please check [Debugging](3-contributing.md#debugging) and
create an issue.
With debugging enabled, there's a chance to find the culprit in the data returned by the myVAILLANT API and fix it.

### Getting Quota Exceeded Errors

If you are getting "Quota Exceeded" errors, you have a few options:

1. Decrease update interval in the integration options. 1800s for live data updates and 7200s for energy data seems save, based on user feedback
2. Disable energy and efficiency sensor that you don't need. Disabled sensors are skipped in the update, and reduce API calls
3. Invite another user in the myVAILLANT app and use that one for the integration. This way at least queries from the mobile app run on a separate account

There's no clear documentation from Vaillant about which API endpoints have quotas, what these quotas are, or how to avoid them.

### Vaillant API is occasionally unavailable

The API this integration uses sometimes goes down. Before reporting an issue, check if the myVAILLANT app works normally.
If it doesn't, there's nothing we can do about it.

### Some features that are available on the controller or in the maintenance settings are not available

If you would like to request a new feature, please check that it's available in the myVAILLANT app first.
Some data (for example quiet mode or legionella protection) are not available in the app, and therefore
can't be supported by this integration.

### The modes in Home Assistant and the myVAILLANT app don't match

Home Assistant has certain pre-defined modes, that can't be changed.
[Check the mapping of modes](2-entities.md#climate-entities) between Home Assistant and myVAILLANT.

### Energy & Efficiency Sensors are delayed / incomplete / behave oddly around midnight

How Vaillant reports energy data, and how Home Assistant deals with sensor data is not a good match:

* Vaillant's API provides energy data in hourly increments, some time after the full hour has passed (let's say at 10:30am for the energy data from 9-10am)
* This integration fetches energy data every hour, for the current day, up to the current time
    * Depending on when your HA schedules this hourly update, it may happen right after Vaillant provides the new hourly data, or almost an hour later
    * Home Assistant doesn't support setting a past date for a sensor reading, the value is always displayed at the time when it was saved
    * Home Assistant also doesn't let you pick when to schedule the hourly update exactly, it depends on when the integration was initialized
    * Data for the whole day is fetched, so that the total is correct even if the API is temporarily unavailable, or the integration misses an hour window for some other reason 
* Worst case, you end up with a 30min delay from Vaillant and a 59min delay from the integration: Your energy data from 9-10am will show up at 11:29am. Best case is probably around 10:30am.
* After midnight, the integration will fetch data for the new day, which will be empty until the first full hour + delay has passed
    * If you have new energy data between 11pm and midnight, it won't show up in your total for the previous day

Home Assistant would need to allow setting a timestamp with each new energy value, to improve this situation.
The delay would still be there, but at least the values would be displayed at the correct time.

You can lower the update interval for fetching energy data, to minimize the delay between Vaillant's updates and HA.
See [Options](#seconds-between-energy-data-updates). But it's not recommended, since it's a lot of data to fetch
and Vaillant may ban you temporarily with 'quota exceeded' errors.

To fix data loss around midnight, the integration could fetch a longer period of time (for example a whole month).
But then the sensor would no longer show a daily total, which would potentially mess with users' setups.
The change from daily to monthly would also show up as a strange spike of energy usage when the update is done. 