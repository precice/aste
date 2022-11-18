#!/bin/bash

set -e -u

# Remove log and json records
rm -f precice*.json
rm -f precice*.log
# Remove precice-run directory
rm -rf precice-run
