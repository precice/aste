#!/usr/bin/env python3
""" Small script to visualize a partition by adding the rank number as Point Data."""

import argparse
import os
from mesh_io import *

parser = argparse.ArgumentParser(description="Visualize partition of a mesh as pointData")
parser.add_argument("meshname", metavar="inputmesh", help="The mesh directory used as input")
parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh name")
args = parser.parse_args()

dirname = args.meshname
i = 0

allpoints = []
allvals = []

while os.path.isfile(dirname + "/" + str(i)):
    filename = dirname + "/" + str(i)
    points, _, _, _ = read_txt(filename)
    allpoints.extend(points)
    allvals.extend([i] * len(points))
    i += 1
filename = args.out_meshname if args.out_meshname else dirname + ".vtk"
write_vtk(filename, allpoints, None, None, allvals)
