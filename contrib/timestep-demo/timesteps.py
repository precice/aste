#!/usr/bin/env python3

import subprocess
import os
if (os.environ.get("ASTEDIR")):
    astedir = os.environ["ASTEDIR"]
else:
    astedir = "." # Set this to the build directory of aste
if (not astedir[-1] == "/"):
    astedir = astedir + "/"

def run(cmd):
    print("+" + cmd)
    subprocess.run(("bash", "-c", cmd))

# Get bunny and red blood cell
if not os.path.isfile("rbc.dt1.vtk"):
    run("wget https://people.sc.fsu.edu/~jburkardt/data/vtk/rbc_001.vtk -O rbc.dt1.vtk")
if not os.path.isfile("bunny.vtk"):
    run("wget https://www.ece.lsu.edu/xinli/Meshing/Data/bunny.vtk -O bunny.vtk")
# Generate 20 timesteps of bunny.vtk
files = ["colored.dt" + str(i) + ".vtk" for i in range(1, 21)]
for t in range(len(files)):
    if not os.path.isfile(files[t]):
        run(astedir + "eval_mesh.py bunny.vtk -o " + files[t] + " " + str(t + 1))
if not all([os.path.isdir("colored.dt"  + str(i)) for i in range(1, 21)]):
    run(astedir + "partition_mesh.py -n 2 " + " ".join(files))
# Partition output mesh as well
run(astedir + "partition_mesh.py -n 2 rbc.dt1.vtk ")
# Run preCICE. Note that the meshes are named colored.dt1, colored.dt2, ...
if not os.path.isdir("vtkA"):
    os.mkdir("vtkA")
if not os.path.isdir("vtkB"):
    os.mkdir("vtkB")
run("mpirun -n 2 " + astedir + "preciceMap -c timesteps-precice.xml -p A --mesh colored&")
run("mpirun -n 2 " + astedir + "preciceMap -c timesteps-precice.xml -p B --mesh rbc --output mapped")

