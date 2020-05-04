#!/usr/bin/env python3
import subprocess
import argparse, logging
import os
import mesh_io
import shutil

# Generate Aste files from preCICE VTK output for every timestep
def main():    
    args=parse_args()
    files = []
    files.append(args.SolverName + ".init.vtk")
    
    for i in range(1,args.n+1):
        if os.path.exists(args.SolverName +".dt" + str(i) + ".vtk"):
            files.append(args.SolverName +".dt" + str(i) + ".vtk")
        else:
            raise Exception(args.SolverName +".dt" + str(i) + ".vtk not found.")
    
    for file in files:
        dirname = os.path.splitext(file)[0]
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)
        points, [], [], pointdata = mesh_io.read_mesh(file, tag=args.tag, datadim=args.datadim)
        mesh_io.write_txt(dirname + "/0", points, pointdata=pointdata)
        
    
    if os.path.exists(args.SolverName + ".dt0"):
        shutil.rmtree(args.SolverName + ".dt0")
        
    print("Renaming " + args.SolverName + ".init to " + args.SolverName +".dt0")
    if os.path.exists(args.SolverName + ".init"):
        os.rename(args.SolverName + ".init", args.SolverName + ".dt0")
    else:
        raise Exception("Initial coupling data " + args.SolverName + ".init does not exist.")

def parse_args():
    parser = argparse.ArgumentParser(description="Convert preCICE VTK exports to ASTE format")
    parser.add_argument("SolverName", 
                        help="""Name of the participant that exported the data. 
                        Files are named SolverName.dti.vtk""")
    parser.add_argument("--ntimesteps", "-n", dest="n", type= int, help="""Number of timesteps""")
    parser.add_argument("--datadim","-d", dest="datadim", type=int, default=1, choices=[1,2,3],
                        help="""Dimension of the coupling data. 
                        Default is 1 (scalar data).""")
    parser.add_argument("--tag", "-t", dest="tag", default=None, help="""Name of the
                        Coupling data in preCICE.""")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
