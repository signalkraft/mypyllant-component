# myPyllant Home Assistant Component

[![GitHub Release](https://img.shields.io/github/release/signalkraft/mypyllant-component.svg)](https://github.com/signalkraft/mypyllant-component/releases)
[![License](https://img.shields.io/github/license/signalkraft/mypyllant-component.svg)](LICENSE)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/signalkraft/mypyllant-component/build-test.yaml)

Home Assistant component that interfaces with the myVAILLANT API (and branded versions of it, such as the MiGo Link app
from Saunier Duval & Bulex).

> [!WARNING] 
> This integration is not affiliated with Vaillant, the developers take no responsibility for anything that happens to
> your devices because of this library.

![myPyllant](https://raw.githubusercontent.com/signalkraft/myPyllant/main/logo.png)

* [Documentation](https://signalkraft.com/mypyllant-component/)
* [Discussion on Home Assistant Community](https://community.home-assistant.io/t/myvaillant-integration/542610)
* [myPyllant Python library](https://github.com/signalkraft/mypyllant)

## Tested Setups

* Vaillant aroTHERM plus heatpump + sensoCOMFORT VRC 720 + sensoNET VR 921
* Vaillant ECOTEC PLUS boiler + VR940F + sensoCOMFORT
* Vaillant ECOTEC PLUS boiler + VRT380f + sensoNET
* Vaillant EcoCompact VSC206 4-5 boiler + Multimatic VRC700/6 + gateway VR920
* Saunier Duval DUOMAX F30 90 + MISET Radio + MiLink V3
* VR42 controllers are also supported
* [More are documented here](https://signalkraft.com/mypyllant-component/#tested-setups)

## Features

![Default Dashboard Screenshot](docs/docs/assets/default-dashboard.png)

* Supports climate & hot water controls, as well as sensor information
* Control operating modes, target temperature, and presets such as holiday more or quick veto
* Set the schedule for climate zones, water heaters, and circulation pumps
  with [a custom service](https://signalkraft.com/mypyllant-component/2-services/#setting-a-time-program)
* Track sensor information of devices, such as temperature, humidity, operating mode, energy usage, or energy efficiency
* See diagnostic information, such as the current heating curve, flow temperature, firmware versions, or water pressure
* Custom services to set holiday mode or quick veto temperature overrides, and their duration

## Installation

### HACS

1. [Install HACS](https://hacs.xyz/docs/setup/download)
2. Search for the myVAILLANT integration in HACS and install it
3. Restart Home Assistant
4. [Add myVaillant integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mypyllant)
5. Sign in with the email & password you used in the myVAILLANT app (or MiGo app for Saunier Duval)

### Manual

1. Download [the latest release](https://github.com/signalkraft/mypyllant-component/releases)
2. Extract the `custom_components` folder to your Home Assistant's config folder, the resulting folder structure should
   be `config/custom_components/mypyllant`
3. Restart Home Assistant
4. [Add myVaillant integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mypyllant), or go to
   Settings > Integrations and add myVAILLANT
5. Sign in with the email & password you used in the myVAILLANT app (or MiGo app for Saunier Duval & Bulex)

## Options

### Seconds between scans

Wait interval between updating (most) sensors. **Don't set this too low, for example 10 leads to quota exceeded errors
and a temporary ban**.

The energy data and efficiency sensors have a fixed hourly interval.

### Delay before refreshing data after updates

How long to wait between making a request (i.e. setting target temperature) and refreshing data.
The Vaillant takes some time to return the updated values.

### Default duration in hours for quick veto

When setting the temperature with the climate controls, the integration uses the "quick veto" feature of the myVAILLANT
app.

With this option you can set for how long the temperature should stay set, before returning to the default value.

### Default duration in days for away mode

When the away mode preset is activated, this duration is used to for the end date (default is 365 days).

### Temperature controls overwrite time program instead of setting quick veto

When raising or lowering the desired temperature in the myVAILLANT app, it sets a quick veto mode for a limited time
with that new temperature, if the zone is in time controlled mode. If you want to permanently change the desired
temperature, you need to update the time schedule.

By default, this integration has the same behavior. But when enabling this option, the Home Assistant climate controls
instead overwrite the temperatures set in the time schedule with the new value (unless quick veto is already active).

### Country

The country you registered your myVAILLANT account in. The list of options is limited to known supported countries.

If a country is missing, please open an issue.

### Brand

Brand of your HVAC equipment and app, pick Saunier Duval if you use the MiGo Link app.

## Known Issues

### Lack of Test Data for Different Systems

Your HVAC system might differ from the ones in `Tested on` above.
If you don't see any entities, or get an error during setup, please check `Debugging` below and create an issue.
With debugging enabled, there's a chance to find the culprit in the data returned by the myVAILLANT API and fix it.

## Entities

You can expect these entities, although names will vary based on your home name (here "Home"),
installed devices (in this example "aroTHERM plus" and "hydraulic station"),
or the naming of your heating zones (in this case "Zone 1"):

| Entity                                                                        | Unit | Class        | Sample          |
|-------------------------------------------------------------------------------|------|--------------|-----------------|
| Home Outdoor Temperature                                                      | °C   | temperature  | 11.2            |
| Home System Water Pressure                                                    | bar  | pressure     | 1.4             |
| Home Firmware Version                                                         |      |              | 0357.40.32      |
| Home Zone 1 (Circuit 0) Desired Temperature                                   | °C   | temperature  | 22.0            |
| Home Zone 1 (Circuit 0) Current Temperature                                   | °C   | temperature  | 22.4            |
| Home Zone 1 (Circuit 0) Humidity                                              | %    | humidity     | 46.0            |
| Home Zone 1 (Circuit 0) Heating Operating Mode                                |      |              | Time Controlled |
| Home Zone 1 (Circuit 0) Heating State                                         |      |              | Idle            |
| Home Zone 1 (Circuit 0) Current Special Function                              |      |              | None            |
| Home Circuit 0 State                                                          |      |              | STANDBY         |
| Home Circuit 0 Current Flow Temperature                                       | °C   | temperature  | 26.0            |
| Home Circuit 0 Heating Curve                                                  |      |              | 1.19            |
| Home Domestic Hot Water 0 Tank Temperature                                    | °C   | temperature  | 49.0            |
| Home Domestic Hot Water 0 Setpoint                                            | °C   | temperature  | 52.0            |
| Home Domestic Hot Water 0 Operation Mode                                      |      |              | Time Controlled |
| Home Domestic Hot Water 0 Current Special Function                            |      |              | Regular         |
| Home Heating Energy Efficiency                                                |      |              | 3.6             |
| Home Device 0 aroTHERM plus Heating Energy Efficiency                         |      |              | 3.6             |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Domestic Hot Water     | Wh   | energy       | 3000.0          |
| Home Device 0 aroTHERM plus Consumed Electrical Energy Heating                | Wh   | energy       | 14000.0         |
| Home Device 0 aroTHERM plus Earned Environment Energy Domestic Hot Water      | Wh   | energy       | 8000.0          |
| Home Device 0 aroTHERM plus Earned Environment Energy Heating                 | Wh   | energy       | 36000.0         |
| Home Device 0 aroTHERM plus Heat Generated Heating                            | Wh   | energy       | 50000.0         |
| Home Device 0 aroTHERM plus Heat Generated Domestic Hot Water                 | Wh   | energy       | 11000.0         |
| Home Device 1 Hydraulic Station Heating Energy Efficiency                     |      |              | unknown         |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Domestic Hot Water | Wh   | energy       | 0.0             |
| Home Device 1 Hydraulic Station Consumed Electrical Energy Heating            | Wh   | energy       | 0.0             |
| Home Zone 1 (Circuit 0) Climate                                               |      |              | auto            |
| Home Away Mode Start Date                                                     |      |              | unknown         |
| Home Away Mode End Date                                                       |      |              | unknown         |
| Home Trouble Codes                                                            |      | problem      | off             |
| Home Online Status                                                            |      | connectivity | on              |
| Home Firmware Update Required                                                 |      | update       | off             |
| Home Firmware Update Enabled                                                  |      |              | on              |
| Home Circuit 0 Cooling Allowed                                                |      |              | off             |
| Home Holiday Duration Remaining                                               | d    |              | 0               |
| Home Domestic Hot Water 0                                                     |      |              | Time Controlled |
| Home Away Mode                                                                |      |              | off             |
| Home Domestic Hot Water 0 Boost                                               |      |              | off             |

## Services

There are custom services for almost every functionality of the myVAILLANT app:

| Name                                                                                                                                                          | Description                                                                     | Target       | Fields                                      |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------|:-------------|:--------------------------------------------|
| [Set quick veto](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_quick_veto)                                              | Sets quick veto temperature with optional duration                              | climate      | Temperature, Duration                       |
| [Set manual mode setpoint](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_manual_mode_setpoint)                          | Sets temperature for manual mode                                                | climate      | Temperature, Type                           |
| [Cancel quick veto](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.cancel_quick_veto)                                        | Cancels quick veto temperature and returns to normal schedule / manual setpoint | climate      |                                             |
| [Set holiday](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_holiday)                                                    | Set holiday / away mode with start / end or duration                            | climate      | Start Date, End Date, Duration              |
| [Cancel Holiday](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.cancel_holiday)                                              | Cancel holiday / away mode                                                      | climate      |                                             |
| [Set Zone Time Program](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_zone_time_program)                                | Updates the time program for a zone                                             | climate      | Type, Time Program                          |
| [Set Water Heater Time Program](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_dhw_time_program)                         | Updates the time program for a water heater                                     | water_heater | Time Program                                |
| [Set Water Heater Circulation Time Program](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_dhw_circulation_time_program) | Updates the time program for the circulation pump of a water heater             | water_heater | Time Program                                |
| [Export Data](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.export)                                                         | Exports data from the mypyllant library                                         |              | Data, Data Resolution, Start Date, End Date |
| [Generate Test Data](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.generate_test_data)                                      | Generates test data for the mypyllant library and returns it as YAML            |              |                                             |
| [Export Yearly Energy Reports](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.report)                                        | Exports energy reports in CSV format per year                                   |              | Year                                        |

Additionally, there are home assistant's built in services for climate controls, water heaters, and switches.

Search for "myvaillant" in Developer Tools > Services in your Home Assistant instance to get the full list plus an
interactive UI.

[![Open your Home Assistant instance and show your service developer tools with a specific service selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_holiday)

## Contributing

See [the docs on contributing](https://signalkraft.com/mypyllant-component/3-contributing/).

### Debugging

When debugging or reporting issues, turn on debug logging by adding this to your `configuration.yaml`
and restarting Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.mypyllant: debug
    myPyllant: debug
```

### Contributing to the underlying mypyllant library

See [this section on the contributing docs](https://signalkraft.com/mypyllant-component/3-contributing/#contributing-to-the-underlying-mypyllant-library).
