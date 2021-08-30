#!/usr/bin/env bash

set -e
set -x

PATH=$(pwd)/../../build:$PATH

APARTS=2
BPARTS=4

# Prepare A meshes for various timesteps
for t in 0 1 2 3; do
  eval_mesh.py 0.004.vtk -o "0.004.d$t.vtk" "$t"
  partition_mesh.py "0.004.d$t.vtk" -n $APARTS
done

partition_mesh.py 0.009.vtk -n $BPARTS

### Map from the bunny to the red blood cell (yeah, that doesn't really make sense)
mpirun -n $APARTS preciceMap -v -p A --mesh 0.004 &
mpirun -n $BPARTS preciceMap -v -p B --mesh 0.009 --output mapped
