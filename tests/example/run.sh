#!/usr/bin/env bash
set -e -x

# Tests the data evaluation as well as preciceMap
# This script assumes the ASTE binaries and python scripts are in $PATH

# Evaluate a predefined function on the coarse mesh
vtk_calculator.py --mesh coarseMesh.vtk --output coarseMeshWithData.vtk --function "franke3d" --data "franke function"

preciceMap -v -p A --mesh coarseMeshWithData --data "franke function" &
preciceMap -v -p B --mesh turbineFine --output mapped --data "result data"


vtk_calculator.py --mesh mapped.vtk --function "franke3d" --diffdata "result data"

