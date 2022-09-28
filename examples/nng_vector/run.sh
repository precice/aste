#!/usr/bin/env bash
set -e -x

# Calculate distance from origin on fine mesh
precice-aste-evaluate -m ../fine_mesh.vtk -f "sin(x)*iHat+cos(y)*jHat+z^2*kHat" -d "MyFunction" -o "fine_mesh_nng.vtk" --gradient

# Map from the finer mesh to coarser mesh
precice-aste-run -v -p A --mesh fine_mesh_nng --data "MyFunction" --vector &
precice-aste-run -v -p B --mesh ../coarse_mesh --output map_nng --data "InterpolatedData" --vector

# Calculate statistics
precice-aste-evaluate -m map_nng.vtk -f "sin(x)*iHat+cos(y)*jHat+z^2*kHat" -d difference --diffdata "InterpolatedData" --diff
