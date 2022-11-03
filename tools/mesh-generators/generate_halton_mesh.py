#!/usr/bin/env python3

import argparse

import numpy as np
import vtk
from scipy.stats.qmc import Halton
from vtk.util.numpy_support import numpy_to_vtk as n2v


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a mesh in unit square or cube, based on Halton sequence"
    )
    parser.add_argument(
        "--mesh",
        "-m",
        dest="output",
        required=True,
        help="The name of the file to create. Must be a .vtk or .vtu file.",
    )
    parser.add_argument(
        "--numpoints",
        "-n",
        type=int,
        dest="num_points",
        default="100",
        help="Number of points to generate.",
    )
    parser.add_argument(
        "--dimension",
        "-d",
        type=int,
        dest="dimension",
        default="2",
        help="Dimension of mesh (2D or 3D).",
    )

    args, _ = parser.parse_known_args()
    return args


def generate_points(dim, num_points):
    points = Halton(d=dim, scramble=False).random(num_points)
    if dim == 2:
        points = np.column_stack((points, np.zeros(num_points)))
    return points


def write_mesh(mesh_filename, points):
    mesh = vtk.vtkUnstructuredGrid()
    point_data = vtk.vtkPoints()
    point_data.SetData(n2v(points))
    mesh.SetPoints(point_data)
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetInputData(mesh)
    writer.SetFileName(mesh_filename)
    writer.Write()


if __name__ == "__main__":
    args = parse_args()
    if args.dimension not in [2, 3]:
        raise ValueError("Dimension must be 2 or 3.")
    points = generate_points(args.dimension, args.num_points)
    write_mesh(args.output, points)
