#!/usr/bin/env python3
"""Evaluates a function on a given mesh, using the VTK Calculator."""

import argparse, logging
import mesh_io
import vtk


def parse_args():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh used as input")
    parser.add_argument("function", 
            help="""The function to evalutate on the mesh. 
            Syntax is the same as used in the calculator object, coordinates are given as e.g. 'coordX'.""")
    parser.add_argument("--out", "-o", dest="out_meshname", help="""The output meshname. 
            Default is the same as for the input mesh""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level. 
            Default is INFO""")

    args = parser.parse_args()
    args.out_meshname = args.out_meshname or args.in_meshname
    return args

def main():
    args = parse_args()
    logging.basicConfig(level = getattr(logging, args.logging))
    data = mesh_io.read_dataset(args.in_meshname)
    logging.info("Read in {} points.".format(data.GetNumberOfPoints()))

    calc = vtk.vtkArrayCalculator()
    calc.SetInputData(data)
    calc.AddCoordinateScalarVariable("coordsX", 0)
    calc.AddCoordinateScalarVariable("coordsY", 1)
    calc.AddCoordinateScalarVariable("coordsZ", 2)
    calc.SetFunction(args.function)
    calc.SetResultArrayName("scalars")
    calc.Update()
    logging.info("Evaluated '{}' on the mesh.".format(args.function))

    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetInputData(calc.GetOutput())
    writer.SetFileName(args.out_meshname)
    writer.Write()
    logging.info("Written output to {}.".format(args.out_meshname))




if __name__ == "__main__":
    main()
