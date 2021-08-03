#!/usr/bin/env bash

set -e
set -x

# This script assumes the ASTE binaries and python scripts are in $PATH
# Furthermore, execute in ./contrib or copy precice.xml from there to $PWD


# Download the red blood cell
test -f rbc.vtk || wget "https://people.sc.fsu.edu/~jburkardt/data/vtk/rbc_001.vtk" -O rbc.vtk

# Download the bunny
test -f bunny.vtk || wget "https://www.ece.lsu.edu/xinli/Meshing/Data/bunny.vtk" -O bunny.vtk

# Evaluate the function x+y on the bunny, write to colored.vtk
eval_mesh.py bunny.vtk -o colored.vtk "x + y"

# Decompose both meshes to two procesors
partition_mesh.py colored.vtk -n 2
partition_mesh.py rbc.vtk -n 2

rm -rf colored.dt0 && mv colored colored.dt0
rm -rf rbc.dt0 && mv rbc rbc.dt0

# The result directory of preciceMap needs to exist beforehand
mkdir -p mapped

# Map from the bunny to the red blood cell (yeah, that doesn't really make sense)
mpirun -n 2 preciceMap -v -p A --mesh colored &
mpirun -n 2 preciceMap -v -p B --mesh rbc --output mapped

# Join the output files together to result.vtk,
# recovering the connectivity from the rbc mesh
# and using all 2 partitions of each mesh.
join_mesh.py -o result.vtk -r rbc.dt0 -n 2 mapped

# Measure the difference between the original function and the mapped values
eval_mesh.py result.vtk -d "x + y"
