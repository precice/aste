#!/usr/bin/env bash
set -e -x

# Calculate franke function on fine mesh
vtk_calculator.py -m ./fine_mesh.vtk -f "franke2d" -d "Franke Function" -o "fine_mesh_lci.vtk"

# Map from the finer mesh to coarser mesh
preciceMap -v -p A --mesh fine_mesh_lci --data "Franke Function" &
preciceMap -v -p B --mesh ./coarse_mesh --output map_nn --data "InterpolatedData"

# Calculate statistics
vtk_calculator.py -m map_nn.vtk -f "franke3d" -d difference --diffdata "InterpolatedData" --diff
