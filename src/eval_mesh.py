#!/usr/bin/env python3
import argparse
import logging
import math
import numpy as np
from multiprocessing import Pool
import mesh_io
import json
import os


def defaultPool():
    try:
        size = int(os.getenv("ASTE_MESH_JOBS"))
        return Pool(size)
    except:
        return Pool()


def relativel2(mesh):
    return math.sqrt(np.nansum(np.square(mesh.data)) / len(mesh.data))


def weightedl2_apply_area(args):
    triangles, vertices = args


    def area(triangle):
        A = vertices[triangle[0]]
        B = vertices[triangle[1]]
        C = vertices[triangle[2]]
        AB = B - A
        AC = C - A
        return np.linalg.norm(np.cross(AB, AC))/2

    return np.apply_along_axis(area, 1, triangles)


def weightedl2(mesh):
    if (not mesh.has_connectivity()):
        return None

    with defaultPool() as pool:
        areas = np.concatenate(pool.map(
            weightedl2_apply_area,
            [(chunk, mesh.points) for chunk in np.array_split(mesh.triangles, os.cpu_count())]
        ))

    weights = np.zeros(len(mesh.points))
    for idx, cell in enumerate(mesh.triangles):
        (a, b, c) = cell
        w = areas[idx]
        weights[a] += w
        weights[b] += w
        weights[c] += w

    return math.sqrt(np.nansum(np.square(mesh.data * weights)))


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    mesh = mesh_io.Mesh.load(args.in_meshname)

    values = user_func(mesh.points, args.function)
    if not args.diff:
        mesh.data = values
    else:
        logging.info("Measuring the error per vertex against mapped data.")
        mesh.data = np.abs(mesh.data - values)

        cnt, min, max = len(mesh.points), np.nanmin(mesh.data), np.nanmax(mesh.data)
        relative, weighted = relativel2(mesh), weightedl2(mesh)
        p99, p95, p90, median = np.percentile(mesh.data, [99, 95, 90, 50])

        logging.info("Vertex count {}".format(cnt))
        logging.info("Relative l2 error {}".format(relative))
        logging.info("Weighted l2 error {}".format(weighted))
        logging.info("Maximum error per vertex {}".format(max))
        logging.info("Minimum error per vertex {}".format(min))
        logging.info("Median error per vertex {}".format(median))
        logging.info("99th percentile of error per vertex {}".format(p99))
        logging.info("95th percentile of error per vertex {}".format(p95))
        logging.info("90th percentile of error per vertex {}".format(p90))

        if args.stats:
            base = os.path.splitext(args.out_meshname)[0]
            json.dump({
                "count": cnt,
                "min": min,
                "max": max,
                "median": median,
                "relative-l2": relative,
                "weighted-l2": weighted,
                "99th percentile": p99,
                "95th percentile": p95,
                "90th percentile": p90
            }, open(base+".stats.json", "w"))

    mesh.save(args.out_meshname)


class Evaluator:
    def __init__(self, func):
        self._func = func

    def evaluate(self, on):
        import math
        i, (x, y, z) = on
        loc_dict = {"x": x, "y": y, "z": z, "math": math, "np": np}
        return eval(self._func, globals(), loc_dict)


def user_func(points, f_str):
    evaluator = Evaluator(f_str)
    with defaultPool() as pool:
        vals = np.array(pool.map(evaluator.evaluate, enumerate(points)), dtype=np.float64)

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
    parser.add_argument("--stats", "-s", action='store_true', help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level.  Default is INFO")

    args = parser.parse_args()
    args.out_meshname = args.out_meshname or args.in_meshname
    return args


if __name__ == "__main__":
    main()
