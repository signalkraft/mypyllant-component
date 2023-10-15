#!/bin/sh

# Used to export the table of entities in the README

ARGS="-o table --table-format=github --columns=Entity=attributes.friendly_name,Unit=attributes.unit_of_measurement,Class=attributes.device_class,Sample=state state list"

hass-cli $ARGS