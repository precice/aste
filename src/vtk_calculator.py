#!/usr/bin/env python3
"""Evaluates a function on a given mesh, using the VTK Calculator."""

import argparse
import logging
import os.path
import vtk
import json
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh (VTK Unstructured Grid) used as input")
    parser.add_argument("function", help="""The function to evalutate on the mesh.
            Syntax is the same as used in the calculator object, coordinates are given as e.g.  'cos(x)+y'.""")
    parser.add_argument("--out", "-o", dest="out_meshname", default=None, help="""The output meshname.
            Default is the same as for the input mesh""")
    parser.add_argument("--tag", "-t", dest="tag", default="MyScalar", help="""The tag for output data.
            Default is MyScalar""")
    parser.add_argument("--intag", "-it", dest="intag", help="""The tag for input data.
            Used in diff mode. If not given tag is used.""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level.
            Default is INFO""")
    parser.add_argument("--diff", "-d", action='store_true', help="Calculate the difference to present data.")
    parser.add_argument("--stats", "-s", action='store_true',
                        help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
    args = parser.parse_args()
    args.out_meshname = args.out_meshname or args.in_meshname
    return args


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))

    assert os.path.isfile(args.in_meshname), "Input mesh file not found!"

    out_meshname = args.out_meshname
    if args.out_meshname is None:
        out_meshname = args.in_meshname

    if args.diff and args.intag is None:
        logging.info("No intag is given outtag '{}' will be used as intag.".format(args.tag))
        intag = args.tag

    reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(args.in_meshname)
    reader.Update()
    vtk_dataset = reader.GetOutput()
    logging.info("Read in {} points.".format(vtk_dataset.GetNumberOfPoints()))

    calc = vtk.vtkArrayCalculator()
    calc.SetInputData(vtk_dataset)
    calc.AddCoordinateScalarVariable("coordsX", 0)
    calc.AddCoordinateScalarVariable("coordsY", 1)
    calc.AddCoordinateScalarVariable("coordsZ", 2)
    calc.SetFunction(args.function)
    calc.SetResultArrayName(args.tag)
    calc.Update()    
    logging.info("Evaluated '{}' on the mesh.".format(args.function))
    
    if args.diff:
        assert args.intag is not None, "Difference mode needs input array tag"

        org_val = []
        calc_val = []
        orgArr = calc.GetOutput().GetPointData().GetAbstractArray(args.intag)
        calcArr = calc.GetOutput().GetPointData().GetAbstractArray(args.tag)
        num_points = vtk_dataset.GetNumberOfPoints()
        for i in range(num_points):
            org_val.append(orgArr.GetTuple1(i))
            calc_val.append(calcArr.GetTuple1(i))
        
        org_val = np.array(org_val)
        calc_val = np.array(calc_val)
        difference = np.abs(org_val - calc_val)
        cnt, min, max = num_points, np.nanmin(difference), np.nanmax(difference)
        p99, p95, p90, median = np.percentile(difference, [99, 95, 90, 50])

        logging.info("Vertex count {}".format(cnt))
        logging.info("Maximum error per vertex {}".format(max))
        logging.info("Minimum error per vertex {}".format(min))
        logging.info("Median error per vertex {}".format(median))
        logging.info("99th percentile of error per vertex {}".format(p99))
        logging.info("95th percentile of error per vertex {}".format(p95))
        logging.info("90th percentile of error per vertex {}".format(p90))

        if args.stats:
            base = os.path.splitext(out_meshname)[0]
            json.dump({
                "count": cnt,
                "min": min,
                "max": max,
                "median": median,
                "99th percentile": p99,
                "95th percentile": p95,
                "90th percentile": p90
            }, open(base + ".stats.json", "w"))

    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetInputData(calc.GetOutput())
    writer.SetFileName(out_meshname)
    writer.Write()
    logging.info("Written output to {}.".format(out_meshname))

if __name__ == "__main__":
    main()
