#!/usr/bin/env python3
import argparse
import logging
import os
import numpy as np
import json
from mesh_io import read_txt, write_mesh, get_cell_type, read_conn


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"

    points, cells, cell_types, values = read_mesh(args.in_meshname, args.numparts, args.recovery)
    print("Points {}\nData\n {}Cells {}\nCelltypes {}\n".format(points, values, cells, cell_types))
    write_mesh(out_meshname, points, cells, cell_types, values)


def join_mesh_partitionwise(dirname, length):
    """
    Partitionn-wise load and append

    This does not contain connectivity.
    The vertex and cell order will be scrambled wrt the original mesh due to the paritioning.
    """
    all_points = []
    all_values = []
    all_cells = []
    all_cell_types = []
    for i in range(length):
        points, cells, cell_types, values = read_txt(os.path.join(dirname, str(i)+".txt"))
        print(len(points))
        offset = len(all_points)
        all_points += points
        all_values += values
        all_cells += [
            tuple(map(lambda idx: idx+offset, cell))
            for cell in cells
        ]
        all_cell_types += cell_types

    assert(len(all_values) in [0, len(all_points)])
    assert(len(all_cell_types) in [0, len(all_cells)])
    return all_points, all_cells, all_cell_types, all_values


def join_mesh_recovery(dirname, length, recoveryPath):
    """
    Parition merge with full recovery

    This uses the originally paritioned mesh as recovery information.
    The result is in the same very order as the original mesh.
    Original cells will be preserved, but will grouped partition-wise.
    Cells between partitions will be appended.
    """
    print("Recovery")
    recoveryFile = os.path.join(recoveryPath, "recovery.json")
    recovery = json.load(open(recoveryFile, "r"))
    mapping = recovery["mapping"]
    size = recovery["size"]
    assert(size == sum(map(len, mapping.values())))

    points = {}
    values = {}
    all_cells = []
    all_cell_types = []

    for i in range(length):
        mapping = {int(key): int(value) for key, value in recovery["mapping"][str(i)].items()}
        partpoints, _, _, partvalues = read_txt(os.path.join(dirname, str(i)+".txt"))
        partcells, partcell_types = read_conn(os.path.join(recoveryPath, str(i)+".conn.txt"))

        for local, point in enumerate(partpoints):
            points[mapping[local]] = point

        for local, value in enumerate(partvalues):
            values[mapping[local]] = value

        all_cells += [
            tuple(map(lambda local: mapping[local], cell))
            for cell in partcells
        ]
        all_cell_types += partcell_types

    all_points = [ point for _, point in sorted(points.items(), key=lambda x: x[0]) ]
    all_values = [ value for _, value in sorted(values.items(), key=lambda x: x[0]) ]

    recovery_cells = [
        tuple(map(int, cell))
        for cell in recovery["cells"]
    ]
    recovery_cell_types = list(map(get_cell_type, recovery_cells))
    all_cells += recovery_cells
    all_cell_types += recovery_cell_types

    assert(len(all_values) in [0, len(all_points)])
    assert(len(all_cell_types) in [0, len(all_cells)])
    return all_points, all_cells, all_cell_types, all_values


def read_mesh(dirname, length = None, recoveryPath = None):
    """
    Reads a mesh from the given directory. If length is given, only the first length parts are read,
    else length is inferred from the files.
    """
    if not length:
        length = 0
        while os.path.isfile(os.path.join(dirname, str(length)+".txt")):
            length += 1
    dirname = os.path.abspath(dirname)
    if not os.path.exists(dirname):
        raise Exception("Directory not found")
    if not os.path.isdir(dirname):
        raise Exception("In mesh must be a directory")

    if recoveryPath is None:
        return join_mesh_partitionwise(dirname, length)
    else:
        return join_mesh_recovery(dirname, length, recoveryPath)



def parse_args():
    parser = argparse.ArgumentParser(description="""Read a partitioned mesh 
            and join it into a .vtk or .txt file.""")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The partitioned mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh. Can be vtk or txt.")
    parser.add_argument("-r", "--recovery", dest="recovery", help="The path to the original partitioned mesh to fully recover it's state.")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, 
            help="The number of parts to read from the input mesh. By default the entire mesh is read.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()


if __name__ == "__main__":
    main()
