#!/usr/bin/env python3
""" Small script to visualize a partition by adding the rank number as Point Data."""

import argparse
import os
from mesh_io import read_txt, write_vtk

parser = argparse.ArgumentParser(description="Visualize partition of a mesh as pointData")
parser.add_argument("meshname", metavar="inputmesh", help="The mesh directory used as input")
parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh name")
args = parser.parse_args()

dirname = args.meshname

allpoints = []
allcells = []
allcell_types = []
allvals = []

i = 0
while os.path.isfile(dirname + "/" + str(i)):
    filename = dirname + "/" + str(i)
    points, cells, cell_types, _ = read_txt(filename)
    assert(len(cells) == len(cell_types))

    offset = len(allpoints)
    allpoints.extend(points)
    allcells.extend([
            tuple(map(lambda idx: idx+offset, cell))
            for cell in cells
        ])
    allcell_types.extend(cell_types)
    allvals.extend([i] * len(points))
    i += 1

assert(len(allpoints) == len(allvals))
assert(len(allcells) == len(allcell_types))
filename = args.out_meshname if args.out_meshname else dirname + ".vtk"
write_vtk(filename, allpoints, allcells, allcell_types, allvals)
