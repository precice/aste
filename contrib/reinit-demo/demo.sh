#!/usr/bin/env bash

set -e
set -x

PATH=$(pwd)/../../build:$PATH

make -j $(nproc) -C $(pwd)/../../build

APARTS=2
BPARTS=4

# Prepare A meshes for various timesteps
for t in 0 1 2 3; do
  eval_mesh.py 0.004.vtk -o "0.004.dt$t.vtk" "$t"
  partition_mesh.py "0.004.dt$t.vtk" -n $APARTS
done

partition_mesh.py 0.009.vtk -n $BPARTS

set -m
(
mpirun -n $APARTS preciceMap -v -p A --mesh "0.004" &
mpirun -n $BPARTS preciceMap -v -p B --mesh "0.009" --output mapped &
wait
)
