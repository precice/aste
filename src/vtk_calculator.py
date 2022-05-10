#!/usr/bin/env python3
import argparse
import json
import logging
from multiprocessing import get_logger
import os.path

import numpy as np
import vtk
import sympy 
from vtk.util.numpy_support import numpy_to_vtk as n2v
from vtk.util.numpy_support import vtk_to_numpy as v2n


class Calculator:
    """Calculator class provided 3 main functionality:
    - Evaluates a given function (scalar or vector) on a given mesh
    - Evaluates difference between a given function \"f\" and given data \"data\" (data-f)
    - Calculate statistics for the difference mentioned above
    - Use \"--help\" argument to see usage
    """

    def __init__(self) -> None:
        args = Calculator.parse_args()
        Calculator.create_logger(args.logging)
        preDefFunctions = Calculator.create_predeffunctions()
        Calculator.evaluate(args, preDefFunctions)

    @staticmethod
    def create_logger(level):
        logger = logging.getLogger('---[ASTE-Calculator]')
        logger.setLevel(getattr(logging, level))
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, level))
        formatter = logging.Formatter('%(name)s %(levelname)s : %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return

    @staticmethod
    def get_logger():
        return logging.getLogger('---[ASTE-Calculator]')

    @staticmethod
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
        parser.add_argument("--gradient","-g",action='store_true',help="Adds array with gradient data")
        parser.add_argument("--stats", "-s", action='store_true',
                            help="Store stats of the difference calculation as the separate file inputmesh.stats.json")
        args, _ = parser.parse_known_args()
        return args

    @staticmethod
    def create_predeffunctions():
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

        return preDefFunctions

    @staticmethod
    def get_function_defitinitions():
        functionDefinitions = {
            "Franke": "Franke's function has two Gaussian peaks of different heights, and a smaller dip.",
            "Eggholder": "A function has many local maxima. It is difficult to optimize.",
            "Rosenbrock": "A function that is unimodal, and the global minimum lies"
            " in a narrow, parabolic valley."}
        return functionDefinitions

    @staticmethod
    def print_predef_functions(preDefFunctions):
        print("Available predefined functions are:")
        longest = max(map(len, preDefFunctions.keys()))
        for name, func in list(preDefFunctions.items()):
            print(f"{name:{longest}} := {func}")
        functionDefinitions = Calculator.get_function_defitinitions()
        print("Definitions of functions are:")
        longest = max(map(len, functionDefinitions.keys()))
        for name, definition in list(functionDefinitions.items()):
            print(f"{name:{longest}} := {definition}")
        return

    @staticmethod
    def evaluate(args, preDefFunctions):
        logger = Calculator.get_logger()
        if args.listfunctions:
            Calculator.print_predef_functions(preDefFunctions)
            return
        assert os.path.isfile(
            args.in_meshname), "Input mesh file not found. Please check your input mesh \"--mesh\"."
        assert args.data, "Dataname \"--data\" is missing. Please give an dataname for given input."

        out_meshname = args.out_meshname
        if args.out_meshname is None:
            logger.info("No output mesh name is given {} will be used.".format(args.in_meshname))
            out_meshname = args.in_meshname

        if args.function in preDefFunctions:
            inputfunc = preDefFunctions[args.function]
        else:
            inputfunc = args.function

        calc = Calculator.create_vtk_calculator()
        if args.diff:
            assert args.diffdata, """The \"--diffdata\" argument is required when running in difference mode (using the \"--diff\" argument).
            Please add a valid \"--diffdata\" argument or type \"--help\" for more information."""

            Calculator.calculate_difference(calc, inputfunc, args, out_meshname)
        else:
            Calculator.calculate_function(calc, inputfunc, args, out_meshname)

    @staticmethod
    def create_vtk_calculator():
        calc = vtk.vtkArrayCalculator()
        calc.AddCoordinateScalarVariable("x", 0)
        calc.AddCoordinateScalarVariable("y", 1)
        calc.AddCoordinateScalarVariable("z", 2)
        return calc

    @staticmethod
    def calculate_function(calc, inputfunc, args, out_meshname):
        logger = Calculator.get_logger()
        vtk_dataset = Calculator.read_mesh(args.in_meshname)
        calc.SetInputData(vtk_dataset)
        calc.SetFunction(inputfunc)
        logger.info("Evaluated \"{}\" on the input mesh \"{}\".".format(inputfunc, args.in_meshname))
        calc.SetResultArrayName(args.data)
        calc.Update()
        vtk_dataset.GetPointData().AddArray(calc.GetOutput().GetPointData().GetAbstractArray(args.data))
        logger.info(f"Evaluated function saved to \"{args.data}\" variable on output mesh \"{out_meshname}\"")
        if args.gradient:
            Calculator.add_gradient(calc,vtk_dataset,inputfunc)
            
        Calculator.write_mesh(vtk_dataset, out_meshname, args.directory)

    @staticmethod
    def calculate_difference(calc, inputfunc, args, out_meshname):
        logger = Calculator.get_logger()
        vtk_dataset = Calculator.read_mesh(args.in_meshname)
        calc.SetInputData(vtk_dataset)
        diffdata = args.diffdata
        if not vtk_dataset.GetPointData().HasArray(diffdata):
            raise Exception(f"Given mesh \"{args.in_meshname}\" has no data with given name \"{diffdata}\"")
        else:
            data = v2n(vtk_dataset.GetPointData().GetAbstractArray(diffdata))
            # Calculate given function on the mesh
        calc.SetFunction(inputfunc)
        calc.SetResultArrayName("function")
        calc.Update()
        func = v2n(calc.GetOutput().GetPointData().GetAbstractArray("function"))
        difference = data - func
        logger.info(f"Evaluated \"{diffdata}\"-\"({inputfunc})\" on the mesh \"{args.in_meshname}\".")

        Calculator.calculate_stats(vtk_dataset, difference, out_meshname, args.stats)

        diff_vtk = n2v(difference)
        diff_vtk.SetName(args.data)
        vtk_dataset.GetPointData().AddArray(diff_vtk)
        Calculator.write_mesh(vtk_dataset, out_meshname, args.directory)

    @staticmethod
    def calculate_stats(vtk_dataset, difference, out_meshname, stats=None):
        logger = Calculator.get_logger()
        # Calculate Statistics
        abs_diff = np.absolute(difference)
        num_points = vtk_dataset.GetNumberOfPoints()
        cnt, abs_min, signed_min, abs_max, signed_max = num_points, np.nanmin(
            abs_diff), np.nanmin(difference), np.nanmax(abs_diff), np.nanmax(difference)
        p99, p95, p90, median = np.percentile(abs_diff, [99, 95, 90, 50])
        relative = np.sqrt(np.nansum(np.square(abs_diff)) / abs_diff.size)
        decorator = 15 * "*"
        spaces = 5 * " "
        logger.info(f"\n\n{decorator}{spaces}Statistics{spaces}{decorator}\n\n")
        logger.info("Vertex count {}".format(cnt))
        logger.info("Relative l2 error {}".format(relative))
        logger.info("Maximum absolute error per vertex {}".format(abs_max))
        logger.info("Maximum signed error per vertex {}".format(signed_max))
        logger.info("Minimum absolute error per vertex {}".format(abs_min))
        logger.info("Minimum signed error per vertex {}".format(signed_min))
        logger.info("Median absolute error per vertex {}".format(median))
        logger.info("99th percentile of absolute error per vertex {}".format(p99))
        logger.info("95th percentile of absolute error per vertex {}".format(p95))
        logger.info("90th percentile of absolute error per vertex {}".format(p90))
        logger.info(f"\n\n{decorator}{spaces}End Statistic{spaces}{decorator}\n\n")

        if stats:
            stat_file = os.path.splitext(out_meshname)[0] + ".stats.json"
            logger.info("Saving stats data to \"{}\"".format(stat_file))
            json.dump({
                "count": cnt,
                "abs_min": abs_min,
                "abs_max": abs_max,
                "signed_min:": signed_min,
                "signed_max": signed_max,
                "median(abs)": median,
                "relative-l2": relative,
                "99th percentile(abs)": p99,
                "95th percentile(abs)": p95,
                "90th percentile(abs)": p90
            }, open(stat_file, "w"))

    @staticmethod
    def read_mesh(in_meshname):
        logger = Calculator.get_logger()
        logger.info(f"Reading input mesh \"{in_meshname}\"")
        extension = os.path.splitext(in_meshname)[1]
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
        reader.SetFileName(in_meshname)
        reader.Update()
        vtk_dataset = reader.GetOutput()
        logger.info("Mesh contains {} points.".format(vtk_dataset.GetNumberOfPoints()))
        return vtk_dataset

    @staticmethod
    def write_mesh(vtk_dataset, out_meshname, directory=None):
        logger = Calculator.get_logger()
        # Create writer
        if os.path.splitext(out_meshname)[1] == ".vtk":
            writer = vtk.vtkUnstructuredGridWriter()
            writer.SetFileTypeToBinary()
        elif os.path.splitext(out_meshname)[1] == ".vtu":
            writer = vtk.vtkXMLUnstructuredGridWriter()
        else:
            raise Exception("Output mesh extension should be '.vtk' and '.vtu'")

        writer.SetInputData(vtk_dataset)
        out_meshname = os.path.basename(os.path.normpath(out_meshname))
        # If directory needed create it
        if directory:
            directory = os.path.abspath(directory)
            os.makedirs(directory, exist_ok=True)
            out_meshname = os.path.join(directory, out_meshname)

        writer.SetFileName(out_meshname)
        writer.Write()
        logger.info(f"Written output to \"{out_meshname}\".")
        
        
    @staticmethod
    def sympy_to_vtk(string):
        return string.replace("**", "^")

    @staticmethod
    def vtk_to_sympy(string):
        return string.replace("^", "**")
    
    @staticmethod
    def add_gradient(calc,vtk_dataset, inputfunc):
        logger = Calculator.get_logger()
        function_in_sympy = sympy.Matrix([sympy.parsing.parse_expr(Calculator.vtk_to_sympy(inputfunc))])
        variables = sympy.Matrix(sympy.symbols('x y z'))
        gradients = [Calculator.sympy_to_vtk(str(x)) for x in function_in_sympy.jacobian(variables)]
        gradient_name_list = ['gradientx','gradienty','gradientz']    
        for name,function in zip(gradient_name_list,gradients):
            calc.SetFunction(function)
            calc.SetResultArrayName(name)
            calc.Update()
            vtk_dataset.GetPointData().AddArray(calc.GetOutput().GetPointData().GetAbstractArray(name))
            logger.info("Evaluated \"{}\" on the input mesh.".format(name))
        return
        
               

if __name__ == "__main__":
    Calculator()
