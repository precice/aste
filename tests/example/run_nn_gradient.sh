#!/usr/bin/env bash
set -e -x

# Calculate franke function on fine mesh
vtk_calculator.py -m fine_mesh.vtk -f "sqrt(x^2+y^2+z^2)" -d "Distance" -o "fine_mesh_nng.vtk" --gradient

# Change config file to run nearest neighbour gradient mapping
sed -i 's/"3"/& experimental=\"true\"/; s/data:scalar name="Data"/& gradient=\"on\"/; s/nearest-neighbor/&-gradient/' precice-config.xml

# Map from the finer mesh to coarser mesh
preciceMap -v -p A --mesh fine_mesh_nng --data "Distance" &
preciceMap -v -p B --mesh coarse_mesh --output map_nng --data "InterpolatedData"

# Calculate statistics
vtk_calculator.py -m map_nng.vtk -f "sqrt(x^2+y^2+z^2)" -d difference --diffdata "InterpolatedData" --diff


# Change config file to original version
sed -i 's/ experimental=\"true\"//; s/ gradient=\"on\"//; s/-gradient//' precice-config.xml
