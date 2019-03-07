#!/usr/bin/env python3
""" Small script to visualize a partition by adding the rank number as Point Data."""

import argparse
import os
from mesh_io import *

parser = argparse.ArgumentParser(description="Visualize partition of a mesh as pointData")
parser.add_argument("meshname", metavar="inputmesh", help="The mesh directory used as input")
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
write_vtk(dirname + ".vtk", allpoints, None, None, allvals)
