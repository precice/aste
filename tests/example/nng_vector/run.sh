#!/usr/bin/env bash
set -e -x

# Calculate distance from origin on fine mesh
vtk_calculator.py -m ../fine_mesh.vtk -f "sin(x)*iHat+cos(y)*jHat+z^2*kHat" -d "MyFunction" -o "fine_mesh_nng.vtk" --gradient

# Map from the finer mesh to coarser mesh
preciceMap -v -p A --mesh fine_mesh_nng --data "MyFunction" --vector &
preciceMap -v -p B --mesh ../coarse_mesh --output map_nng --data "InterpolatedData" --vector

# Calculate statistics
vtk_calculator.py -m map_nng.vtk -f "sin(x)*iHat+cos(y)*jHat+z^2*kHat" -d difference --diffdata "InterpolatedData" --diff
