#!/usr/bin/env python3
import argparse
import logging
import os
import numpy as np
from mesh_io import read_txt, write_mesh


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    points, cells, cell_types, values = read_mesh(args.in_meshname, args.numparts)
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"
    write_mesh(out_meshname, points, cells, cell_types, values)


def read_mesh(dirname, length = None):
    """
    Reads a mesh from the given directory. If length is given, only the first length parts are read, 
    else length is inferred from the files. 
    """
    if not length:
        length = 0
        while os.path.isfile(os.path.join(dirname, str(length))):
            length += 1
    dirname = os.path.abspath(dirname)
    if not os.path.exists(dirname):
        raise Exception("Directory not found")
    all_points = []
    all_values = []
    all_cells = []
    all_cell_types = []
    for i in range(length):
        points, cells, cell_types, values = read_txt(os.path.join(dirname, str(i)))
        offset = len(all_points)
        all_points += points
        all_values += values
        all_cells += [
            tuple(map(lambda idx: idx+offset, cell))
            for cell in cells
        ]
        all_cell_types += cell_types
    return all_points, all_cells, all_cell_types, all_values


def parse_args():
    parser = argparse.ArgumentParser(description="""Read a partitioned mesh 
            and join it into a .vtk or .txt file.""")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The partitioned mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh. Can be vtk or txt.")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, 
            help="The number of parts to read from the input mesh. By default the entire mesh is read.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()


if __name__ == "__main__":
    main()
