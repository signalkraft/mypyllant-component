#!/bin/bash

tar zxvf docker/config.tar.gz -C docker
cp -r custom_components/mypyllant docker/config/custom_components
cp -r ../myPyllant/src/myPyllant docker/myPyllant
docker compose up