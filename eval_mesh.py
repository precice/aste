#!/usr/bin/env python3
import logging
import os
import numpy as np
import argparse
from mesh_io import *

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    points, cells, cell_types, _ = read_mesh(args.in_meshname)
    points = np.array(points)
    values = user_func(points, args.f_str)
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname[:-4] + ".txt"
    write_mesh(out_meshname, points, cells, cell_types, values)

def user_func(points, f_str = None):
    if not f_str:
        f_str = "y = np.zeros(len(x))"
    x = np.array(points)
    loc_dict = {"x": x}
    exec(f_str, globals(), loc_dict)
    y = loc_dict["y"]
    if y is None:
        raise Exception("Invalid function. y was not assigned a value")
    if len(y) != len(x):
        raise Exception("Invalid function. y has wrong shape.")
    return y

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a function on a given mesh")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh used as input")
    parser.add_argument("--func", "-f", dest="f_str", help="The function to evalutate on the mesh. Points are given in the form \"x = [[x1,y1,z1],[x2,y2,z2],...]\" as a numpy array. Output must be written to \"y\". Default is the 0 function.")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output meshname. Default is the same as for the input mesh")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()

if __name__ == "__main__":
    main()
