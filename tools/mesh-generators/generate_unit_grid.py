import argparse
import itertools

import meshio
import numpy as np


def generate_unit_grid(out, x, y, z):
    assert x > 0, "x needs to be positive"
    assert y > 0, "y needs to be positive"
    assert z > 0, "z needs to be positive"

    xs = np.linspace(0, 1, x)
    ys = np.linspace(0, 1, y)
    zs = np.linspace(0, 1, z)

    coords = [tuple(reversed(t)) for t in itertools.product(zs, ys, xs)]
    mesh = meshio.Mesh(coords, [])
    mesh.write(out)


def parse_args():
    parser = argparse.ArgumentParser(description="__doc__")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--mesh",
        "-m",
        dest="output",
        help="The name of the file to create. Must be supported by meshio.",
    )
    parser.add_argument(
        "-x",
        dest="x",
        default=10,
        type=int,
        help="Amount of grid points in x direction",
    )
    parser.add_argument(
        "-y",
        dest="y",
        default=10,
        type=int,
        help="Amount of grid points in y direction",
    )
    parser.add_argument(
        "-z", dest="z", default=1, type=int, help="Amount of grid points in z direction"
    )

    args, _ = parser.parse_known_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    generate_unit_grid(args.output, args.x, args.y, args.z)
