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

mv -f colored colored.dt0
mv -f rbc rbc.dt0

# Map from the bunny to the red blood cell (yeah, that doesn't really make sense)
mpirun -n 2 preciceMap -v -p A --mesh colored &
mpirun -n 2 preciceMap -v -p B --mesh rbc --output mapped

# Join the output files together to result.vtk
join_mesh.py mapped -o result.vtk
