#!/usr/bin/env bash
set -e -x

# Calculate distance from origin on fine mesh
precice-aste-evaluate.py -m ../fine_mesh.vtk -f "sqrt(x^2+y^2+z^2)" -d "Distance" -o "fine_mesh_nng.vtk" --gradient

# Map from the finer mesh to coarser mesh
precice-aste-run -v -p A --mesh fine_mesh_nng --data "Distance" &
precice-aste-run -v -p B --mesh ../coarse_mesh --output map_nng --data "InterpolatedData"

# Calculate statistics
precice-aste-evaluate.py -m map_nng.vtk -f "sqrt(x^2+y^2+z^2)" -d difference --diffdata "InterpolatedData" --diff
