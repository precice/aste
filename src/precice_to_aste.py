#!/usr/bin/env python3
import subprocess
import argparse, logging

def run(cmd):
    print("+ " + cmd)
    subprocess.run(cmd, shell = True, check = True)
    
# Generate Aste files from preCICE VTK output for every timestep
def main():    
    args=parse_args()
    files = []
    files.append(args.SolverName + ".init.vtk")
    
    for i in range(1,args.n+1):
        files.append(args.SolverName +".dt" + str(i) + ".vtk")
    
    for i in files:
        run("partition_mesh.py -n 1 " + i + " -t " + args.function + " --datadim "+ str(args.datadim))
    
    run("rm -r " + args.SolverName + ".dt0")
    run("mv " + args.SolverName + ".init " + args.SolverName + ".dt0")

def parse_args():
    parser = argparse.ArgumentParser(description="Convert preCICE VTK exports to ASTE format")
    parser.add_argument("SolverName", 
                        help="""Name of the participant that exported the data. 
                        Files are named SolverName.dti.vtk""")
    parser.add_argument("--ntimesteps", "-n", dest="n", type= int, help="""Number of timesteps""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level. 
            Default is INFO""")
    parser.add_argument("--datadim","-d", dest="datadim", default="1", choices=["1","2", "3"],
                        help="""Dimension of the coupling function. 
                        Default is 1 (scalar function).""")
    parser.add_argument("--function", "-f", dest="function", default=None, help="""Name of the
                        Coupling function in preCICE.""")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
