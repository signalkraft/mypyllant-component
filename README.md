# myPyllant Home Assistant Component

[![GitHub Release](https://img.shields.io/github/release/signalkraft/mypyllant-component.svg)](https://github.com/signalkraft/mypyllant-component/releases)
[![License](https://img.shields.io/github/license/signalkraft/mypyllant-component.svg)](LICENSE)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/signalkraft/mypyllant-component/build-test.yaml)

Home Assistant component that interfaces with the myVAILLANT API (and branded versions of it, such as the MiGo Link app from Saunier Duval).

![myPyllant](https://raw.githubusercontent.com/signalkraft/myPyllant/main/logo.png)

* [Documentation](http://signalkraft.com/mypyllant-component/)
* [Discussion on Home Assistant Community](https://community.home-assistant.io/t/myvaillant-integration/542610)
* [myPyllant Python library](https://github.com/signalkraft/mypyllant)

## Tested Setups

* Vaillant aroTHERM plus heatpump + sensoCOMFORT VRC 720 + sensoNET VR 921
* Vaillant ECOTEC PLUS boiler + VR940F + sensoCOMFORT
* Vaillant ECOTEC PLUS boiler + VRT380f + sensoNET
* Saunier Duval DUOMAX F30 90 + MISET Radio + MiLink V3

Not affiliated with Vaillant, the developers take no responsibility for anything that happens to your devices 
because of this library.

## Features

![Screenshot](https://raw.githubusercontent.com/signalkraft/mypyllant-component/main/screenshot.png)

* Supports climate & hot water controls, as well as sensor information
* Control operating modes, target temperature, and presets such as holiday more or quick veto
* Track sensor information of devices, such as temperature, humidity, operating mode, energy usage, or energy efficiency
* See diagnostic information, such as the current heating curve, flow temperature, or water pressure
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
2. Extract the `custom_components` folder to your Home Assistant's config folder, the resulting folder structure should be `config/custom_components/mypyllant`
3. Restart Home Assistant
4. [Add myVaillant integration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mypyllant), or go to Settings > Integrations and add myVAILLANT
5. Sign in with the email & password you used in the myVAILLANT app (or MiGo app for Saunier Duval)

## Options

### Seconds between scans

Wait interval between updating (most) sensors. The energy data and efficiency sensors have a fixed hourly interval.

### Delay before refreshing data after updates

How long to wait between making a request (i.e. setting target temperature) and refreshing data.
The Vaillant takes some time to return the updated values.

### Default duration in hours for quick veto

When setting the temperature with the climate controls, the integration uses the "quick veto" feature of the myVAILLANT app.

With this option you can set for how long the temperature should stay set, before returning to the default value.

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

You can expect these entities, although names may vary based on your installed devices (in this example "aroTHERM plus" 
and "Hydraulic Station") or the naming of your heating zones (in this case "Zone 1"):

| Entity                       | Unit   | Class   | Sample   |
|------------------------------|--------|---------|----------|
| Cooling Allowed in Circuit 0 |        |         | off      |
| Error sensoCOMFORT         |  | problem      | off |
| Online Status sensoCOMFORT |  | connectivity | on  |
| Cooling Allowed in Circuit 0 |  |  | off |
| Zone 1 |  |  | auto |
| aroTHERM plus Consumed Electrical Energy Domestic Hot Water | Wh | energy |   0   |
| aroTHERM plus Consumed Electrical Energy Heating            | Wh | energy |   0   |
| aroTHERM plus Earned Environment Energy Domestic Hot Water  | Wh | energy |   0   |
| aroTHERM plus Earned Environment Energy Heating             | Wh | energy | 334.5 |
| aroTHERM plus Heat Generated Heating                        | Wh | energy | 334.5 |
| aroTHERM plus Heat Generated Domestic Hot Water             | Wh | energy |   0   |
| Hydraulic Station Consumed Electrical Energy Domestic Hot Water | Wh | energy | 0 |
| Heating Energy Efficiency |  |  | 4 |
| Cooling Allowed in Circuit 0               |    |             | off     |
| Current Flow Temperature in Circuit 0      | °C | temperature | 22.0    |
| Heating Curve in Circuit 0                 |    |             | 0.8     |
| Min Flow Temperature Setpoint in Circuit 0 | °C | temperature | 35.0    |
| State in Circuit 0                         |    |             | STANDBY |
| Desired Temperature in Zone 1      | °C | temperature | 0.0             |
| Current Temperature in Zone 1      | °C | temperature | 18.5            |
| Humidity in Zone 1                 | %  | humidity    | 60.0            |
| Heating Operating Mode in Zone 1   |    |             | Time Controlled |
| Heating State in Zone 1            |    |             | Idle            |
| Current Special Function in Zone 1 |    |             | None            |
| Tank Temperature Domestic Hot Water 255         | °C | temperature | 47.0            |
| Setpoint Domestic Hot Water 255                 | °C | temperature | 49.0            |
| Operation Mode Domestic Hot Water 255           |    |             | Time Controlled |
| Current Special Function Domestic Hot Water 255 |    |             | Regular         |
| Domestic Hot Water 0 |  |  | Time Controlled |
| Outdoor Temperature | °C | temperature | 2.29 |
| System Mode |  |  | REGULAR |
| Water Pressure | bar | pressure | 1.4 |

## Services

There are custom services to control holiday mode and quick veto temperatures for each climate zone.
Search for "myvaillant" in Developer Tools > Services in your Home Assistant instance to get the full list plus an interactive UI.

[![Open your Home Assistant instance and show your service developer tools with a specific service selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=mypyllant.set_holiday)

## Contributing

> **Warning**
> 
> You need at least Python 3.10.

Fork and clone this repo, then from the root directory run:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.test.txt
pre-commit install
# Make your changes
pytest
git commit ...
```

If you also need to modify the underlying [myPyllant library](https://github.com/signalkraft/mypyllant),
clone & install it in editable mode in `mypyllant-component`:

```shell
# From the root of this repository
git clone https://github.com/signalkraft/myPyllant.git ../myPyllant
pip install -e ../myPyllant
```

Now you can modify `myPyllant/src` and directly develop against these changes in `mypyllant-component`.

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

See https://github.com/signalkraft/mypyllant#contributing