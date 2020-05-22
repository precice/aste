#!/usr/bin/env python3
import argparse
import logging
import os
import numpy as np
import json
from mesh_io import read_txt, write_mesh, get_cell_type


def findRecoveryFile(meshname):
    if os.path.isdir(meshname):
        file = os.path.join(meshname, "recovery.json")
        if os.path.isfile(file):
            logging.info("Using recovery file {}".format(file))
            return file
    return None


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"
    recoveryFile = args.recovery if args.recovery else findRecoveryFile(args.in_meshname)

    points, cells, cell_types, values = read_mesh(args.in_meshname, args.numparts, recoveryFile)
    write_mesh(out_meshname, points, cells, cell_types, values)


def read_mesh(dirname, length = None, recoveryFile = None):
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
    if not os.path.isdir(dirname):
        raise Exception("In mesh must be a directory")

    all_points = []
    all_values = []
    all_cells = []
    all_cell_types = []
    if recoveryFile:
        recovery = json.load(open(recoveryFile, "r"))
        mapping = recovery["mapping"]
        size = recovery["size"]
        assert(size == sum(map(len, mapping.values())))

        points = {}
        values = {}

        for i in range(length):
            mapping = recovery["mapping"][str(i)]
            partpoints, partcells, partcell_types, partvalues = read_txt(os.path.join(dirname, str(i)))

            for local, point in enumerate(partpoints):
                points[mapping[str(local)]] = point

            for local, value in enumerate(partvalues):
                values[mapping[str(local)]] = value

            all_cells += [
                tuple(map(lambda local: mapping[str(local)], cell))
                for cell in partcells
            ]
            all_cell_types += partcell_types

        all_points = [ point for _, point in sorted(points.items(), key=lambda x: x[0]) ]
        all_values = [ value for _, value in sorted(values.items(), key=lambda x: x[0]) ]
        all_cells += [
            tuple(map(int, cell))
            for cell in recovery["cells"]
        ]
        all_cell_types += map(get_cell_type, recovery["cells"])
    else:
        # Partitionn-wise load and append
        # This does not contain connectivity between
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

    assert(len(all_values) in [0, len(all_points)])
    assert(len(all_cell_types) in [0, len(all_cells)])
    return all_points, all_cells, all_cell_types, all_values


def parse_args():
    parser = argparse.ArgumentParser(description="""Read a partitioned mesh 
            and join it into a .vtk or .txt file.""")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The partitioned mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh. Can be vtk or txt.")
    parser.add_argument("-r", "--recovery", dest="recovery", help="The receovery file of the partitionned mesh.")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, 
            help="The number of parts to read from the input mesh. By default the entire mesh is read.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()


if __name__ == "__main__":
    main()
