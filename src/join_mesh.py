#!/usr/bin/env python3
import argparse
import logging
import os
import numpy as np
import json
from mesh_io import read_txt, get_cell_type, read_conn
import mesh_io


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"

    mesh = read_mesh(args.in_meshname, args.numparts, args.recovery)
    print("Joined mesh: {}".format(mesh))
    mesh.save(out_meshname)


def join_mesh_partitionwise(dirname, length):
    """
    Partitionn-wise load and append

    This does not contain connectivity.
    The vertex and cell order will be scrambled wrt the original mesh due to the paritioning.
    """
    logging.info("Starting patitionwise mesh merge")
    accumulated = mesh_io.Mesh()
    for i in range(length):
        mesh = mesh_io.Mesh.load(os.path.join(dirname, str(i)+".txt"))
        accumulated.append(mesh)
    return accumulated


def join_mesh_recovery(dirname, partitions, recoveryPath):
    """
    Parition merge with full recovery

    This uses the originally paritioned mesh as recovery information.
    The result is in the same very order as the original mesh.
    Original cells will be preserved, but will grouped partition-wise.
    Cells between partitions will be appended.
    """
    logging.info("Starting mesh recovery")
    recoveryFile = os.path.join(recoveryPath, "recovery.json")
    recovery = json.load(open(recoveryFile, "r"))
    mapping = recovery["mapping"]
    size = recovery["size"]
    assert(size == sum(map(len, mapping.values())))

    points = {}
    values = {}
    all_cells = []

    for i in range(partitions):
        logging.debug("Processing parititon {}".format(i))
        partmapping = {int(key): int(value) for key, value in recovery["mapping"][str(i)].items()}

        partfile = os.path.join(dirname, str(i)+".txt")
        partconnfile = os.path.join(recoveryPath, str(i)+".conn.txt")
        logging.debug("Partition mesh file: "+partfile)
        logging.debug("Recovery connectivity file: "+partconnfile)
        partpoints, _, _, partvalues = read_txt(partfile)
        partcells, _ = read_conn(partconnfile)

        for local, point in enumerate(partpoints):
            points[partmapping[local]] = point

        for local, value in enumerate(partvalues):
            values[partmapping[local]] = value

        all_cells += [
            tuple(map(lambda local: partmapping[local], cell))
            for cell in partcells
        ]

    logging.debug("Recovering point order")
    all_points = [ point for _, point in sorted(points.items(), key=lambda x: x[0]) ]
    all_values = [ value for _, value in sorted(values.items(), key=lambda x: x[0]) ]

    logging.debug("Recovering inter-partition connectivity")
    recovery_cells = [
        tuple(map(int, cell))
        for cell in recovery["cells"]
    ]
    recovery_cell_types = list(map(get_cell_type, recovery_cells))
    all_cells += recovery_cells

    assert(len(all_values) in [0, len(all_points)])

    logging.info("Assembling recovered mesh")
    return mesh_io.Mesh(all_points, all_values, all_cells)


def count_partitions(dirname):
    detected = 0
    while True:
        partitionFile = os.path.join(dirname, str(detected)+".txt")
        if (not os.path.isfile(partitionFile)):
            break
        detected += 1
    return detected


def read_mesh(dirname, partitions = None, recoveryPath = None):
    """
    Reads a mesh from the given directory.
    """
    if not partitions:
        partitions = count_partitions(dirname)
        logging.debug("Detected "+str(partitions)+" partitions from directory "+dirname)
    dirname = os.path.abspath(dirname)
    if not os.path.exists(dirname):
        raise Exception("Directory not found")
    if not os.path.isdir(dirname):
        raise Exception("In mesh must be a directory")
    if partitions == 0:
        raise Exception("No partitions found")

    if recoveryPath is None:
        return join_mesh_partitionwise(dirname, partitions)
    else:
        return join_mesh_recovery(dirname, partitions, recoveryPath)



def parse_args():
    parser = argparse.ArgumentParser(description="Read a partitioned mesh and join it into a .vtk or .txt file.")
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
