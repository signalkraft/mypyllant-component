#!/bin/sh

# Used to export the table of entities in the README

ARGS="-o table --table-format=github --columns=Entity=attributes.friendly_name,Unit=attributes.unit_of_measurement,Class=attributes.device_class,Sample=state state list"

hass-cli $ARGS "binary_sensor.circuit*"
hass-cli --no-headers $ARGS "binary_sensor.control*" | tail -n +2
hass-cli --no-headers $ARGS "binary_sensor.circuit*" | tail -n +2
hass-cli --no-headers $ARGS "climate.zone*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.arotherm*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.hydraulic*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.heating_energy_efficiency" | tail -n +2
hass-cli --no-headers $ARGS "sensor.*circuit*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.*zone*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.*_255" | tail -n +2
hass-cli --no-headers $ARGS "water_heater.domestic_hot_water*" | tail -n +2
hass-cli --no-headers $ARGS "sensor.outdoor_temperature" | tail -n +2
hass-cli --no-headers $ARGS "sensor.system_mode" | tail -n +2
hass-cli --no-headers $ARGS "sensor.*water_pressure*" | tail -n +2
