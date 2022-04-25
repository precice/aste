#!/usr/bin/env bash
set -e -x

# Calculate franke function on fine mesh
vtk_calculator.py -m fine_mesh.vtk -f "franke3d" -d "Franke Function"

# Map from the finer mesh to coarser mesh
preciceMap -v -p A --mesh fine_mesh --data "Franke Function" &
preciceMap -v -p B --mesh coarse_mesh --output map --data "InterpolatedData"

# Calculate statistics
vtk_calculator.py -m map.vtk -f "franke3d" -d difference --diffdata "InterpolatedData" --diff
