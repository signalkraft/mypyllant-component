#!/bin/bash

# Run command in .venv if found, otherwise fll back to globally installed (for Github actions)
CMD=".venv/bin/$1"
if [ -f "$CMD" ]; then
    $CMD "${@:2}"
else
    "$1" "${@:2}"
fi