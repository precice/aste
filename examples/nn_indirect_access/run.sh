#!/usr/bin/env bash
set -e -x

# Calculate franke function on fine mesh
precice-aste-evaluate -m ../fine_mesh.vtk -f "franke3d" -d "Franke Function" -o "fine_mesh_nn.vtk"

# Map from the finer mesh to coarser mesh
precice-aste-run -v -p A --mesh fine_mesh_nn --data "Franke Function" &
precice-aste-run -v -p B --mesh ../coarse_mesh --output map_nn --data "InterpolatedData" --indirect-read 0

# Calculate statistics
precice-aste-evaluate -m map_nn.vtk -f "franke3d" -d difference --diffdata "InterpolatedData" --diff
