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


class Calculator:
    """Calculator class provided 3 main functionality:
    - Evaluates a given function (scalar or vector) on a given mesh
    - Evaluates difference between a given function \"f\" and given data \"data\" (data-f)
    - Calculate statistics for the difference mentioned above
    - Use \"--help\" argument to see usage
    """

    def __init__(self) -> None:
        self.args = None
        self.calc = None
        self.functionDefinitions = None
        self.inputfunc = None
        self.logger = None
        self.out_meshname = None
        self.preDefFunctions = None

        self.parse_args()
        self.create_logger()
        self.create_predeffunctions()
        self.create_vtk_calculator()
        self.evaluate()

    def create_logger(self):
        logging.basicConfig(level=getattr(logging, self.args.logging))
        self.logger = logging

    def parse_args(self):
        parser = argparse.ArgumentParser(description=__doc__)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--mesh", "-m", dest="in_meshname",
                           help="The mesh (VTK Unstructured Grid) used as input")
        parser.add_argument("--function", "-f", dest="function", default="eggholder3d",
                            help="""The function to evalutate on the mesh.
                Syntax is the same as used in the calculator object, coordinates are given as e.g.  'cos(x)+y'.
                Alternatively, you can use predefined function
                Default is Eggholder function in 3D (eggholder3d).""")
        group.add_argument("--list-functions", dest="listfunctions", action="store_true",
                           help="Prints list of predefined functions.")
        parser.add_argument("--output", "-o", dest="out_meshname", default=None, help="""The output meshname.
                Default is the same as for the input mesh""")
        parser.add_argument("--data", "-d", dest="data", help="The name of output data.")
        parser.add_argument("--diffdata", "-diffd", dest="diffdata", help="""The name of difference data.
                Required in diff mode.""")
        parser.add_argument("--log", "-l", dest="logging", default="INFO",
                            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level.
                Default is INFO""")
        parser.add_argument("--directory", "-dir", dest="directory", default=None,
                            help="Directory for output files (optional)")
        parser.add_argument(
            "--diff",
            action='store_true',
            help="Calculate the difference between \"--diffdata\" and the specified"
            "function \"--function\"")
        parser.add_argument("--stats", "-s", action='store_true',
                            help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
        self.args, _ = parser.parse_known_args()

    def create_predeffunctions(self):
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
            f"{name}({arg})": self.twoDFunctions[name].format(first=arg[0], second=arg[1])
            for name in ["franke2d", "eggholder2d", "rosenbrock2d"]
            for arg in ["xy", "xz", "yz"]
        }

        self.preDefFunctions = {
            "franke3d": "0.75*exp(-((9*x-2)^2+(9*y-2)^2+(9*z-2)^2)/4)"
            "+0.75*exp(-(9*x+1)^2/49-(9*y+1)/10-(9*z+1)/10)"
            "+0.5*exp(-((9*x-7)^2+(9*y-3)^2+(9*y-5)^2)/4)"
            "-0.2*exp(-(9*x-4)^2-(9*y-7)^2-(9*z-5)^2)",
            "eggholder3d": "-x*sin(sqrt(abs(x-y-47)))-(y+47)*sin(sqrt(abs(0.5*x+y+47)))"
                        "-y*sin(sqrt(abs(y-z-47)))-(z+47)*sin(sqrt(abs(0.5*y+z+47)))",
            "rosenbrock3d": "(100*(y-x^2)^2+(x-1)^2)+(100*(z-y^2)^2+(y-1)^2)"
        }

        self.preDefFunctions.update(preDef2DFunctions)

        self.functionDefinitions = {
            "Franke": "Franke's function has two Gaussian peaks of different heights, and a smaller dip.",
            "Eggholder": "A function has many local maxima. It is difficult to optimize.",
            "Rosenbrock": "A function that is unimodal, and the global minimum lies"
            " in a narrow, parabolic valley."}

    def print_predef_functions(self):
        print("Available predefined functions are:")
        longest = max(map(len, self.preDefFunctions.keys()))
        for name, func in list(self.preDefFunctions.items()):
            print(f"{name:{longest}} := {func}")
        print("Definitions of functions are:")
        longest = max(map(len, self.functionDefinitions.keys()))
        for name, definition in list(self.functionDefinitions.items()):
            print(f"{name:{longest}} := {definition}")
        return

    def evaluate(self):
        if self.args.listfunctions:
            self.print_predef_functions()
            return
        assert os.path.isfile(
            self.args.in_meshname), "Input mesh file not found. Please check your input mesh \"--mesh\"."
        assert self.args.data, "Dataname \"--data\" is missing. Please give an dataname for given input."

        self.out_meshname = self.args.out_meshname
        if self.args.out_meshname is None:
            self.logger.info("No output mesh name is given {} will be used.".format(self.args.in_meshname))
            self.out_meshname = self.args.in_meshname

        if self.args.function in self.preDefFunctions:
            self.inputfunc = self.preDefFunctions[self.args.function]
        else:
            self.inputfunc = self.args.function

        if self.args.diff:
            assert self.args.diffdata, """The \"--diffdata\" argument is required when running in difference mode (using the \"--diff\" argument).
            Please add a valid \"--diffdata\" argument or type \"--help\" for more information."""

            self.calculate_difference()
        else:
            self.calculate_function()

    def create_vtk_calculator(self):
        self.calc = vtk.vtkArrayCalculator()
        self.calc.AddCoordinateScalarVariable("x", 0)
        self.calc.AddCoordinateScalarVariable("y", 1)
        self.calc.AddCoordinateScalarVariable("z", 2)

    def set_vtk_calculator_input(self, vtk_dataset):
        self.calc.SetInputData(vtk_dataset)

    def calculate_function(self):
        vtk_dataset = self.read_mesh()
        self.set_vtk_calculator_input(vtk_dataset)
        self.calc.SetFunction(self.inputfunc)
        self.logger.info("Evaluated \"{}\" on the input mesh \"{}\".".format(self.inputfunc, self.args.in_meshname))
        self.calc.SetResultArrayName(self.args.data)
        self.calc.Update()
        self.logger.info(
            f"Evaluated function saved to \"{self.args.data}\" variable on output mesh \"{self.out_meshname}\"")
        self.write_mesh(self.calc.GetOutput())

    def calculate_difference(self):
        vtk_dataset = self.read_mesh()
        self.set_vtk_calculator_input(vtk_dataset)
        diffdata = self.args.diffdata
        if not vtk_dataset.GetPointData().HasArray(diffdata):
            raise Exception(f"Given mesh \"{self.args.in_meshname}\" has no data with given name \"{diffdata}\"")
        else:
            data = v2n(vtk_dataset.GetPointData().GetAbstractArray(diffdata))
            # Calculate given function on the mesh
        self.calc.SetFunction(self.inputfunc)
        self.calc.SetResultArrayName("function")
        self.calc.Update()
        func = v2n(self.calc.GetOutput().GetPointData().GetAbstractArray("function"))
        difference = data - func
        self.logger.info(f"Evaluated \"{diffdata}\"-\"({self.inputfunc})\" on the mesh \"{self.args.in_meshname}\".")

        self.calculate_stats(vtk_dataset, difference)

        diff_vtk = n2v(difference)
        diff_vtk.SetName(self.args.data)
        vtk_dataset.GetPointData().AddArray(diff_vtk)
        self.write_mesh(vtk_dataset)

    def calculate_stats(self, vtk_dataset, difference):
        # Calculate Statistics
        num_points = vtk_dataset.GetNumberOfPoints()
        cnt, min, max = num_points, np.nanmin(difference), np.nanmax(difference)
        p99, p95, p90, median = np.percentile(difference, [99, 95, 90, 50])
        relative = np.sqrt(np.nansum(np.square(difference)) / difference.size)
        self.logger.info("Vertex count {}".format(cnt))
        self.logger.info("Relative l2 error {}".format(relative))
        self.logger.info("Maximum error per vertex {}".format(max))
        self.logger.info("Minimum error per vertex {}".format(min))
        self.logger.info("Median error per vertex {}".format(median))
        self.logger.info("99th percentile of error per vertex {}".format(p99))
        self.logger.info("95th percentile of error per vertex {}".format(p95))
        self.logger.info("90th percentile of error per vertex {}".format(p90))

        if self.args.stats:
            stat_file = os.path.splitext(self.out_meshname)[0] + ".stats.json"
            self.logger.info("Saving stats data to \"{}\"".format(stat_file))
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

    def read_mesh(self):
        self.logger.info(f"Reading input mesh \"{self.args.in_meshname}\"")
        extension = os.path.splitext(self.args.in_meshname)[1]
        if (extension == ".vtu"):
            reader = vtk.vtkXMLUnstructuredGridReader()
        elif (extension == ".vtk"):
            reader = vtk.vtkUnstructuredGridReader()
            reader.ReadAllScalarsOn()
            reader.ReadAllVectorsOn()
            reader.ReadAllFieldsOn()
        else:
            raise Exception(
                "Unkown input file extension please check your input file or hype \"--help\" for more information.")
        reader.SetFileName(self.args.in_meshname)
        reader.Update()
        vtk_dataset = reader.GetOutput()
        self.logger.info("Mesh contains {} points.".format(vtk_dataset.GetNumberOfPoints()))
        return vtk_dataset

    def write_mesh(self, vtk_dataset):
        # Create writer
        if os.path.splitext(self.out_meshname)[1] == ".vtk":
            writer = vtk.vtkUnstructuredGridWriter()
            writer.SetFileTypeToBinary()
        elif os.path.splitext(self.out_meshname)[1] == ".vtu":
            writer = vtk.vtkXMLUnstructuredGridWriter()
        else:
            raise Exception("Output mesh extension should be '.vtk' and '.vtu'")

        writer.SetInputData(vtk_dataset)

        out_meshname = os.path.basename(os.path.normpath(self.out_meshname))
        # If directory needed create it
        if self.args.directory:
            directory = os.path.abspath(self.args.directory)
            os.makedirs(directory, exist_ok=True)
            out_meshname = os.path.join(directory, out_meshname)

        writer.SetFileName(out_meshname)
        writer.Write()
        self.logger.info(f"Written output to \"{out_meshname}\".")


if __name__ == "__main__":
    Calculator()
