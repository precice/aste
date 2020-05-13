#!/usr/bin/env python3
import argparse, logging, math
import numpy as np
from multiprocessing import Pool
from mesh_io import read_mesh, write_mesh
import math


def relativel2(pointdata):
    return math.sqrt(np.sum(np.square(pointdata)) / len(pointdata))


def weightedl2(points, cells, values):
    vertices = np.array(points)
    triangles = np.array(cells, dtype=np.int_)

    def area(triangle):
        A = vertices[triangle[0]]
        B = vertices[triangle[1]]
        C = vertices[triangle[2]]
        AB = B - A
        AC = C - A
        return  np.linalg.norm(np.cross(AB, AC))/2

    areas = np.apply_along_axis(area, 1, triangles)

    weights = np.zeros(len(vertices))
    for idx in range(len(triangles)):
        (a, b, c) = triangles[idx]
        w = areas[idx]
        weights[a] += w
        weights[b] += w
        weights[c] += w

    return math.sqrt(np.sum(np.square(np.array(values) * weights)))


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    points, cells, cell_types, pointdata = read_mesh(args.in_meshname)
    points = np.array(points)
    values = user_func(points, args.function)
    if args.diff:
        values = np.abs(np.array(pointdata) - values)
        logging.info("Relative l2 error {}".format(relativel2(pointdata)))
        logging.info("Weighted l2 error {}".format(weightedl2(points, cells, pointdata)))
        logging.info("Maximum error {}".format(np.nanmax(values)))
        logging.info("Minimum error {}".format(np.nanmin(values)))
        p99, p95, p90, median = np.percentile(values, [99, 95, 90, 50])
        logging.info("Median error {}".format(median))
        logging.info("99th percentile of error {}".format(p99))
        logging.info("95th percentile of error {}".format(p95))
        logging.info("90th percentile of error {}".format(p90))

    write_mesh(args.out_meshname, points, cells, cell_types, abs(values))


class Evaluator:
    def __init__(self, func):
        self._func = func;

    def evaluate(self, on):
        i, (x, y, z) = on
        loc_dict = {"x": x, "y": y, "z": z, "math": math, "np": np}
        return eval(self._func, globals(), loc_dict)


def user_func(points, f_str):
    import math
    points = np.array(points)
    evaluator = Evaluator(f_str)
    with Pool() as pool:
        vals = np.array(pool.map(evaluator.evaluate, enumerate(points)))

    logging.info("Evaluated {} on {} vertices".format(f_str, len(vals)))
    return vals


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a function on a given mesh")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh used as input")
    parser.add_argument("function", 
            help="""The function to evalutate on the mesh. 
            Points are given in the form \"(x, y, z)\". An example for a function would be
            \"math.sin(x) + math.exp(z)\".""")
    parser.add_argument("--out", "-o", dest="out_meshname", help="""The output meshname. 
            Default is the same as for the input mesh""")
    parser.add_argument("--diff", "-d", action='store_true', help="Calculate the difference to present data.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level. 
            Default is INFO""")

    args = parser.parse_args()
    args.out_meshname = args.out_meshname or args.in_meshname
    return args


if __name__ == "__main__":
    main()
