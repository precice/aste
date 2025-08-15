#!/bin/bash

set -e -u

cd "$(dirname "$0")"

# Run Fluid Side
precice-aste-run --aste-config aste-config-fluid.json &

# Run Solid Side
precice-aste-run --aste-config aste-config-solid.json
