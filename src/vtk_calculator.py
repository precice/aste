#!/usr/bin/env python3
import argparse
import logging
import os.path
import vtk
import json
import sys
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy as v2n
from vtk.util.numpy_support import numpy_to_vtk as n2v

"""Evaluates a function on a given mesh, using the VTK Calculator."""

"""
This calculator can calculate vector or scalar field on given mesh.

Example usage

Scalar calculation and writing to given file

./vtk_calculator.py inputmesh.vtk exp(cos(x)+sin(y)) -t e^(cos(x)+sin(y)) -o outputmesh.vtk

Vector field and appends to input mesh

./vtk_calculator.py inputmesh.vtk x*iHat+cos(y)*jHat-sin(z)*kHat -t MyVectorField

There is also a diff mode which provides statistic between input data and function calculated
(Note that it only works for scalar data)

./vtk_calculator.py -m inputmesh.vtu -f x+y -d mydata --diff --stats

Calculates difference between given function and mydata data save over rides into variable data and saves statistics

./vtk_calculator.py -m inputmesh.vtu -f x+y -d diffence -diffd mydata --diff

Calculates difference between given function and mydata data save into diffence data

"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", "-m", dest="in_meshname", required=True,
                        help="The mesh (VTK Unstructured Grid) used as input")
    parser.add_argument("--function", "-f", dest="function", required=True,
                        help="""The function to evalutate on the mesh.
            Syntax is the same as used in the calculator object, coordinates are given as e.g.  'cos(x)+y'.""")
    parser.add_argument("--output", "-o", dest="out_meshname", default=None, help="""The output meshname.
            Default is the same as for the input mesh""")
    parser.add_argument("--data", "-d", dest="data", default="MyData", help="""The name of output data.
            Default is MyData""")
    parser.add_argument("--diffdata", "-diffd", dest="diffdata", help="""The name of difference data.
            Used in diff mode. If not given, output data is used.""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level.
            Default is INFO""")
    parser.add_argument("--directory", "-dir", dest="directory", default=None,
                        help="Directory for output files (optional)")
    parser.add_argument("--diff", action='store_true', help="Calculate the difference to present data.")
    parser.add_argument("--stats", "-s", action='store_true',
                        help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))

    assert os.path.isfile(args.in_meshname), "Input mesh file not found!"

    out_meshname = args.out_meshname
    if args.out_meshname is None:
        logging.info("No output mesh name is given {} will be used.".format(args.in_meshname))
        out_meshname = args.in_meshname

    if args.diff and args.diffdata is None:
        logging.info("No input dataname is given outdata '{}' will be used as input dataname.".format(args.data))
        diffdata = args.data
    else:
        diffdata = args.diffdata

    extension = os.path.splitext(args.in_meshname)[1]
    if (extension == ".vtu"):
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif (extension == ".vtk"):
        reader = vtk.vtkUnstructuredGridReader()
    else:
        print("Unkown input file extension please check your input file.")
        os.exit()
    reader.SetFileName(args.in_meshname)
    reader.Update()
    vtk_dataset = reader.GetOutput()
    logging.info("Mesh contains {} points.".format(vtk_dataset.GetNumberOfPoints()))

    calc = vtk.vtkArrayCalculator()
    calc.SetInputData(vtk_dataset)
    calc.AddCoordinateScalarVariable("x", 0)
    calc.AddCoordinateScalarVariable("y", 1)
    calc.AddCoordinateScalarVariable("z", 2)
    if args.diff:
        # Check VTK file has dataname
        if not vtk_dataset.GetPointData().HasArray(diffdata):
            logging.warning(
                "Given mesh \"{}\" has no data with given name \"{}\".\nABORTING!\n".format(
                    args.in_meshname, diffdata))
            sys.exit()
        else:
            data = v2n(vtk_dataset.GetPointData().GetAbstractArray(diffdata))
        # Calculate given function on the mesh
        calc.SetFunction(args.function)
        calc.SetResultArrayName("function")
        calc.Update()
        func = v2n(calc.GetOutput().GetPointData().GetAbstractArray("function"))
        difference = data - func
        logging.info("Evaluated \"{}\"-\"({})\" on the mesh \"{}\".".format(diffdata, args.function, args.in_meshname))

        # Calculate Statistics
        num_points = vtk_dataset.GetNumberOfPoints()
        cnt, min, max = num_points, np.nanmin(difference), np.nanmax(difference)
        p99, p95, p90, median = np.percentile(difference, [99, 95, 90, 50])
        relative = np.sqrt(np.nansum(np.square(difference)) / difference.size)

        logging.info("Vertex count {}".format(cnt))
        logging.info("Relative l2 error {}".format(relative))
        logging.info("Maximum error per vertex {}".format(max))
        logging.info("Minimum error per vertex {}".format(min))
        logging.info("Median error per vertex {}".format(median))
        logging.info("99th percentile of error per vertex {}".format(p99))
        logging.info("95th percentile of error per vertex {}".format(p95))
        logging.info("90th percentile of error per vertex {}".format(p90))

        if args.stats:
            stat_file = os.path.splitext(out_meshname)[0] + ".stats.json"
            logging.info("Saving stats data to \"{}\"".format(stat_file))
            json.dump({
                "count": cnt,
                "min": min,
                "max": max,
                "median": median,
                "relative-l2": relative,
                "99th percentile": p99,
                "95th percentile": p95,
                "90th percentile": p90
            }, open(stat_file, "w"))

    else:
        calc.SetFunction(args.function)
        logging.info("Evaluated \"{}\" on the input mesh \"{}\".".format(args.function, args.in_meshname))
        calc.SetResultArrayName(args.data)
        calc.Update()

    logging.info("Evaluated function saved to \"{}\" variable on output mesh \"{}\"".format(args.data, out_meshname))

    if os.path.splitext(out_meshname)[1] == ".vtk":
        writer = vtk.vtkUnstructuredGridWriter()
    elif os.path.splitext(out_meshname)[1] == ".vtu":
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Output mesh extension should be '.vtk' and '.vtu'")

    if args.diff:
        diff_vtk = n2v(difference)
        diff_vtk.SetName(args.data)
        num_comp = diff_vtk.GetNumberOfComponents()
        if num_comp > 1:
            vtk_dataset.GetPointData().SetVectors(diff_vtk)
        else:
            vtk_dataset.GetPointData().SetScalars(diff_vtk)
        writer.SetInputData(vtk_dataset)
    else:
        writer.SetInputData(calc.GetOutput())

    out_meshname = os.path.basename(os.path.normpath(out_meshname))
    if args.directory:
        directory = os.path.abspath(args.directory)
        os.makedirs(directory, exist_ok=True)
        out_meshname = os.path.join(directory, out_meshname)

    writer.SetFileName(out_meshname)
    writer.SetFileTypeToBinary()
    writer.Write()
    logging.info("Written output to \"{}\".".format(out_meshname))


if __name__ == "__main__":
    main()
