#!/usr/bin/env python3
# This script assumes the ASTE binaries and python scripts are in $PATH
# Furthermore, execute in ./contrib/timestep-demo or copy precice.xml from there to $PWD

import os, subprocess

def run(cmd):
    print("+ " + cmd)
    subprocess.run(cmd, shell = True, check = True)

# Get bunny and red blood cell
if not os.path.isfile("rbc.dt0.vtk"):
    run("wget --quiet https://people.sc.fsu.edu/~jburkardt/data/vtk/rbc_001.vtk -O rbc.dt0.vtk")
    
if not os.path.isfile("bunny.vtk"):
    run("wget --quiet https://www.ece.lsu.edu/xinli/Meshing/Data/bunny.vtk -O bunny.vtk")
    
# Generate 20 timesteps of bunny.vtk
files = ["colored.dt" + str(i) + ".vtk" for i in range(20)]
for t, f in enumerate(files):
    if not os.path.isfile(f):
        run("eval_mesh.py bunny.vtk -o " + f + " " + str(t))
        
if not all([os.path.isdir("colored.dt"  + str(i)) for i in range(20)]):
    run("partition_mesh.py -n 2 " + " ".join(files))
    
# Partition output mesh as well
run("partition_mesh.py -n 2 rbc.dt0.vtk ")

# Run preCICE. Note that the meshes are named colored.dt1, colored.dt2, ...
os.makedirs("vtkA", exist_ok = True)
os.makedirs("vtkB", exist_ok = True)

run("mpirun -n 2 preciceMap -v -c precice.xml -p A --mesh colored &")
run("mpirun -n 2 preciceMap -v -c precice.xml -p B --mesh rbc --output mapped")

