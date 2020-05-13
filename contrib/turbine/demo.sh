#!/usr/bin/env bash

set -e
set -x

# This script assumes the ASTE binaries and python scripts are in $PATH
# Furthermore, execute in ./contrib or copy precice.xml from there to $PWD


# Download the red blood cell
#test -f rbc.vtk || wget "https://people.sc.fsu.edu/~jburkardt/data/vtk/rbc_001.vtk" -O rbc.vtk

# Download the bunny
#test -f bunny.vtk || wget "https://www.ece.lsu.edu/xinli/Meshing/Data/bunny.vtk" -O bunny.vtk

# Evaluate the function x+y on the bunny, write to colored.vtk
python3 ../../src/eval_mesh.py coarseMesh.vtk -o coarseMeshWithData.vtk "y"

# Decompose both meshes to two procesors
python3 ../../src/partition_mesh.py coarseMeshWithData.vtk -n 2 > log.coarse
python3 ../../src/partition_mesh.py turbineFine.vtk -n 4 > log.fine

#rm -rf colored.dt0 && mv colored colored.dt0
#rm -rf rbc.dt0 && mv rbc rbc.dt0

### Map from the bunny to the red blood cell (yeah, that doesn't really make sense)
mpirun -n 2 ../../build/preciceMap -v -p A --mesh coarseMeshWithData &
mpirun -n 4 ../../build/preciceMap -v -p B --mesh turbineFine --output mapped

### Join the output files together to result.vtk
python3 ../../src/join_mesh.py mapped -i turbineFine.vtk -o result.vtk

python3 ../../src/eval_mesh.py --diff -o difference.vtk result.vtk "y"

