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
from sympy import *

"""Evaluates a function on a given mesh, using the VTK Calculator."""

"""
This calculator can calculate vector or scalar field on given mesh.

Example usage

Scalar calculation and writing to given file

vtk_calculator.py -m inputmesh.vtk -f "exp(cos(x)+sin(y))" --data "e^(cos(x)+sin(y))" -o outputmesh.vtk

Vector field calculation and appends to input mesh

vtk_calculator.py -m "inputmesh.vtk" -f "x*iHat+cos(y)*jHat-sin(z)*kHat" -d "MyVectorField"

There is also a diff mode which provides statistic between input data and function calculated
(Note that it only works for scalar data)

For example to calculate difference between given function "x+y"
and existing data "sin(x)" and override the result to "sin(x)" and to save statistics into a file
following command is used.

vtk_calculator.py -m inputmesh.vtu -f "x+y" -d "sin(x)" --diff --stats

If you don't want to override "sin(x)" and prefer to save the newly generated
data into another variable "difference" following command can be used.

vtk_calculator.py -m inputmesh.vtu -f "x+y" -d "difference" --diffdata "sin(x)" --diff --stats
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mesh", "-m", dest="in_meshname",
                        help="The mesh (VTK Unstructured Grid) used as input")
    parser.add_argument("--function", "-f", dest="function", default="eggholder3d",
                        help="""The function to evalutate on the mesh.
            Syntax is the same as used in the calculator object, coordinates are given as e.g.  'cos(x)+y'.
            Alternatively, you can use predefined function
            Default is Eggholder function in 3D (eggholder3d).""")
    group.add_argument("--list-functions", dest="listfunctions",action="store_true", help="Prints list of predefined functions.")
    parser.add_argument("--output", "-o", dest="out_meshname", default=None, help="""The output meshname.
            Default is the same as for the input mesh""")
    parser.add_argument("--data", "-d", dest="data", default="MyData", help="""The name of output data.
            Default is \"MyData\".""")
    parser.add_argument("--diffdata", "-diffd", dest="diffdata", help="""The name of difference data.
            Used in diff mode. If not given, output data is used.""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level.
            Default is INFO""")
    parser.add_argument("--directory", "-dir", dest="directory", default=None,
                        help="Directory for output files (optional)")
    parser.add_argument("--diff", action='store_true',
                        help="Calculate the difference to present data.")
    parser.add_argument("--stats", "-s", action='store_true',
                        help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
    parser.add_argument("--gradient", "-g", action='store_true',
                        help="Adds array with the gradient data")
    args = parser.parse_args()
    return args


twoDFunctions = {
    "franke2d": "0.75*exp(-((9*{first}-2)^2+(9*{second}-2)^2)/4)"
    "+0.75*exp(-(9*{first}+1)^2/49-(9*{second}+1)/10)"
    "+0.5*exp(-((9*{first}-7)^2+(9*{second}-3)^2)/4)"
    "-0.2*exp(-(9*{first}-4)^2-(9*{second}-7)^2)",
    "eggholder2d": "-{first}*sin(sqrt(abs({first}-{second}-47)))"
    "-({second}+47)*sin(sqrt(abs(0.5*{first}+{second}+47)))",
    "rosenbrock2d": "(100*({second}-{first}^2)^2+({first}-1)^2)"
}

preDef2DFunctions = {
    f"{name}({arg})": twoDFunctions[name].format(first=arg[0], second=arg[1])
    for name in ["franke2d", "eggholder2d", "rosenbrock2d"]
    for arg in ["xy", "xz", "yz"]
}

preDefFunctions = {
    "franke3d": "0.75*exp(-((9*x-2)^2+(9*y-2)^2+(9*z-2)^2)/4)"
    "+0.75*exp(-(9*x+1)^2/49-(9*y+1)/10-(9*z+1)/10)"
    "+0.5*exp(-((9*x-7)^2+(9*y-3)^2+(9*y-5)^2)/4)"
    "-0.2*exp(-(9*x-4)^2-(9*y-7)^2-(9*z-5)^2)",
    "eggholder3d": "-x*sin(sqrt(abs(x-y-47)))-(y+47)*sin(sqrt(abs(0.5*x+y+47)))"
                   "-y*sin(sqrt(abs(y-z-47)))-(z+47)*sin(sqrt(abs(0.5*y+z+47)))",
    "rosenbrock3d": "(100*(y-x^2)^2+(x-1)^2)+(100*(z-y^2)^2+(y-1)^2)"
}

preDefFunctions.update(preDef2DFunctions)


functionDefinitions = {
    "Franke": "Franke's function has two Gaussian peaks of different heights, and a smaller dip.",
    "Eggholder": "A function has many local maxima. It is difficult to optimize.",
    "Rosenbrock": "A function that is unimodal, and the global minimum lies"
    " in a narrow, parabolic valley."}


def print_predef_functions():
    print("Available predefined functions are:")
    longest = max(map(len, preDefFunctions.keys()))
    for name, func in list(preDefFunctions.items()):
        print(f"{name:{longest}} := {func}")
    print("Definitions of functions are:")
    longest = max(map(len, functionDefinitions.keys()))
    for name, definition in list(functionDefinitions.items()):
        print(f"{name:{longest}} := {definition}")
    return

def main(args):
    logging.basicConfig(level=getattr(logging, args.logging))

    if args.listfunctions:
        print_predef_functions()
        return

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

    if args.function in preDefFunctions:
        inputfunc = preDefFunctions[args.function]
    else:
        inputfunc = args.function

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
        calc.SetFunction(inputfunc)
        calc.SetResultArrayName("function")
        calc.Update()
        func = v2n(calc.GetOutput().GetPointData().GetAbstractArray("function"))
        difference = data - func
        logging.info("Evaluated \"{}\"-\"({})\" on the mesh \"{}\".".format(diffdata, inputfunc, args.in_meshname))

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
        calc.SetFunction(inputfunc)
        logging.info("Evaluated \"{}\" on the input mesh \"{}\".".format(inputfunc, args.in_meshname))
        calc.SetResultArrayName(args.data)
        calc.Update()

    logging.info("Evaluated function saved to \"{}\" variable on output mesh \"{}\"".format(args.data, out_meshname))

    if os.path.splitext(out_meshname)[1] == ".vtk":
        writer = vtk.vtkUnstructuredGridWriter()
        writer.SetFileTypeToBinary()
    elif os.path.splitext(out_meshname)[1] == ".vtu":
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Output mesh extension should be '.vtk' and '.vtu'")

    if args.diff:
        diff_vtk = n2v(difference)
        diff_vtk.SetName(args.data)
        vtk_dataset.GetPointData().AddArray(diff_vtk)
        writer.SetInputData(vtk_dataset)
    else:
        writer.SetInputData(calc.GetOutput())

    out_meshname = os.path.basename(os.path.normpath(out_meshname))
    if args.directory:
        directory = os.path.abspath(args.directory)
        os.makedirs(directory, exist_ok=True)
        out_meshname = os.path.join(directory, out_meshname)

    writer.SetFileName(out_meshname)
    writer.Write()
    logging.info("Written output to \"{}\".".format(out_meshname))
    return


def sympy_to_vtk(string):
    s = string
    s = s.replace("**", "^")
    return s


def vtk_to_sympy(string):
    s = string
    s = s.replace("^", "**")
    return s


def add_gradient(args):

    function = args.function
    func = parse_expr(vtk_to_sympy(function))

    out = args.out_meshname
    if args.directory:
        out = args.directory + "/" + args.out_meshname

    args.gradient = False
    args.in_meshname = out
    args.out_meshname = None

    x = Symbol('x')
    grad_dx = func.diff(x)
    args.data = 'gradientdx'
    args.function = sympy_to_vtk(str(grad_dx))
    main(args)

    y = Symbol('y')
    grad_dy = func.diff(y)
    args.data = 'gradientdy'
    args.function = sympy_to_vtk(str(grad_dy))
    main(args)

    z = Symbol('z')
    grad_dz = func.diff(z)
    args.data = 'gradientdz'
    args.function = sympy_to_vtk(str(grad_dz))
    main(args)


if __name__ == "__main__":

    args = parse_args()
    main(args)

    if args.gradient:
        add_gradient(args)
