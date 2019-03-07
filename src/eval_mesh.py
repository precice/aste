#!/usr/bin/env python3
import argparse, logging, math
import numpy as np
from mesh_io import *

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    points, cells, cell_types, _ = read_mesh(args.in_meshname)
    points = np.array(points)
    values = user_func(points, args.function)
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname
    write_mesh(out_meshname, points, cells, cell_types, values)

def user_func(points, f_str):
    points = np.array(points)
    vals = np.zeros(points.shape[0])
    for i, (x, y, z) in enumerate(points):
        loc_dict = {"x": x, "y": y, "z": z, "math": math, "np": np}
        vals[i] = eval(f_str, globals(), loc_dict)
        logging.debug("Evaluating {} on ({}, {}, {}) = {}".format(f_str, x, y, z, vals[i]))

    logging.info("Evaluated {} on {} vertices".format(f_str, len(vals)))
    return vals

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a function on a given mesh")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh used as input")
    parser.add_argument("function", 
            help="""The function to evalutate on the mesh. 
            Points are given in the form \"(x, y, z)\". An example for a function would be
            \"math.sin(x) + math.exp(z)\".""")
    parser.add_argument("--out", "-o", dest="out_meshname", help="""The output meshname. 
            Default is the same as for the input mesh""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level. 
            Default is INFO""")
    return parser.parse_args()

if __name__ == "__main__":
    main()
