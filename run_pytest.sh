#!/bin/sh

# Run pytest in .venv if found, otherwise fll back to globally installed (for Github actions)
PYTEST=.venv/bin/pytest
if [ -f "$PYTEST" ]; then
    $PYTEST "$@"
else
    pytest "$@"
fi