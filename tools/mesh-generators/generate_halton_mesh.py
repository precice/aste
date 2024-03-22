#!/usr/bin/env python3

import argparse
import os

import meshio
import numpy as np
from scipy.spatial import Delaunay
from scipy.stats.qmc import Halton


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
    parser.add_argument(
        "--seed", "-s", type=int, dest="seed", help="Seed for random number generator."
    )
    parser.add_argument(
        "--connectivity", "-c", action="store_true", help="Generate connectivity"
    )

    args, _ = parser.parse_known_args()
    return args


def generate_points(dim, num_points, seed):
    points = Halton(d=dim, scramble=False, seed=seed).random(num_points)
    if dim == 2:
        points = np.column_stack((points, np.zeros(num_points)))
    return points


def write_mesh(mesh_filename, points, cells):
    mesh = meshio.Mesh(points, cells)
    mesh.write(mesh_filename)


def get_trianglation(points, dim):
    if dim == 2:
        return ("triangle", Delaunay(points[:, :-1]).simplices)
    else:
        return ("tetra", Delaunay(points).simplices)


if __name__ == "__main__":
    args = parse_args()
    if args.dimension not in [2, 3]:
        raise ValueError("Dimension must be 2 or 3.")
    _, ext = os.path.splitext(args.output)
    if ext.lower() != ".vtk" and ext.lower() != ".vtu":
        raise ValueError("Output file must be a .vtk or .vtu file.")
    points = generate_points(args.dimension, args.num_points, args.seed)
    cells = [("vertex", np.arange(points.shape[0]).reshape(-1, 1))]
    if args.connectivity:  # Generate connectivity
        cells.append(get_trianglation(points, args.dimension))
    write_mesh(args.output, points, cells)
