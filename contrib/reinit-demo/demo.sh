#!/usr/bin/env bash

set -e
set -x

# Make sure the build is uptodate
make -j $(nproc) -C $(pwd)/../../build
PATH=$(pwd)/../../build:$PATH

# Define the amount of partitions of A and B parti
APARTS=2
BPARTS=4

# Prepare A meshes for various timesteps
eval_mesh.py 0.004.vtk -o "0.004.dt0.vtk" "0.78 + math.cos(10*(x+y+z))"
partition_mesh.py "0.004.dt0.vtk" -n $APARTS
for t in 1 2 3; do
  rm -rf ./0.004.dt$t/
  cp -r ./0.004.dt0/ 0.004.dt$t
done

# Prepare B mesh
partition_mesh.py 0.009.vtk -n $BPARTS

# Run in a group
set -m
(
mpirun -n $APARTS preciceMap -v -p A --mesh "0.004" &
mpirun -n $BPARTS preciceMap -v -p B --mesh "0.009" --output mapped &
wait
)

# Post process the results
join_mesh.py -o mapped.vtk -r 0.009 mapped
eval_mesh.py mapped.vtk -o error.vtk --diff "0.78 + math.cos(10*(x+y+z))"
