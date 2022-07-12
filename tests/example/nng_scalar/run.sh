#!/usr/bin/env bash
set -e -x

# Calculate distance from origin on fine mesh
vtk_calculator.py -m ../fine_mesh.vtk -f "sqrt(x^2+y^2+z^2)" -d "Distance" -o "fine_mesh_nng.vtk" --gradient

# Map from the finer mesh to coarser mesh
preciceMap -v -p A --mesh fine_mesh_nng --data "Distance" &
preciceMap -v -p B --mesh ../coarse_mesh --output map_nng --data "InterpolatedData"

# Calculate statistics
vtk_calculator.py -m map_nng.vtk -f "sqrt(x^2+y^2+z^2)" -d difference --diffdata "InterpolatedData" --diff
