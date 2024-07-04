#!/bin/bash

set -e

# config contains a basic HA setup and HACS
PYTHON_LIB_DIR="$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")"
rm -rf /config/custom_components
tar zxvf /tmp/config.tar.gz -C /
apk add --update envsubst
envsubst < /config/.storage/core.config_entries.template > /config/.storage/core.config_entries
# Copies custom component and library into docker (to avoid permission of mounting volumes directly)
cp -r /tmp/myPyllant "$PYTHON_LIB_DIR"
chattr +i -R "$PYTHON_LIB_DIR/myPyllant"
mkdir -p /config/custom_components
cp -r /tmp/mypyllant-component /config/custom_components/mypyllant
/init python -m homeassistant --config /config