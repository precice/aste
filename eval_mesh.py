#!/usr/bin/python3
import os
import vtk
import numpy as np
import argparse
from tqdm import tqdm

def main():
    args = parse_args()
    points, vtkmesh = read_mesh(args.in_meshname)
    points = np.array(points)
    values = user_func(points, args.f_str)
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname[:-4] + ".txt"
    write_mesh(points, values, out_meshname, vtkmesh, args.data_tag)

def user_func(points, f_str = None):
    if not f_str:
        f_str = "y = np.zeros(len(x))"
    x = points
    loc_dict = {"x": x}
    exec(f_str, globals(), loc_dict)
    y = loc_dict["y"]
    if y is None:
        raise Exception("Invalid function. y was not assigned a value")
    if len(y) != len(x):
        raise Exception("Invalid function. y has wrong shape.")
    return y

def write_mesh(points, values, out_meshname, vtkmesh = None, data_tag = "Values"):
    if out_meshname[-4:] == ".vtk":
        write_vtk(out_meshname, vtkmesh, values, data_tag) 
    elif out_meshname[-4:] == ".txt":
        write_txt(out_meshname, points, values)
    else:
        raise Exception("Unrecognized file extension: " + out_meshname[-4:])
def write_vtk(out_meshname, vtkmesh, values, data_tag):
    scalars = vtk.vtkDoubleArray()
    scalars.SetName(data_tag)
    for i, val in enumerate(values):
        scalars.InsertTuple1(i, val)
    pointData = vtkmesh.GetPointData()
    pointData.SetScalars(scalars)
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(out_meshname)
    writer.SetInputData(vtkmesh)
    writer.Write()

def write_txt(out_meshname, points, values):
    with open(out_meshname, "w") as fh:
        for i, point in enumerate(points):
            for j in range(3):
                fh.write(str(point[j]) + " ")
            fh.write(str(float(values[i])) + "\n")


def read_mesh(filename):
    """
    Reads a mesh from the given filename and returns a list of all points read. For vtk meshes the vtkDataSet is returned as well.
    """
    if filename[-4:] == ".vtk":
        result = []
        reader = vtk.vtkDataSetReader()
        reader.SetFileName(filename)
        reader.Update()
        output = reader.GetOutput()
        return [output.GetPoint(i) for i in range(output.GetNumberOfPoints())], output
    elif filename[-4:] == ".txt":
        points = []
        with open(filename, "r") as fh:
            for line in tqdm(fh, "Reading lines"):
                point = ()
                parts = line.split(" ")
                for i in range(3):
                    point += (float(parts[i]),)
                points.append(point)
        return points, None

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a function on a given mesh")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The mesh used as input")
    parser.add_argument("--func", "-f", dest="f_str", help="The function to evalutate on the mesh. Points are given in the form \"x = [[x1,y1,z1],[x2,y2,z2],...]\" as a numpy array. Output must be written to \"y\". Default is the 0 function.")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output meshname. Default is the input mesh")
    parser.add_argument("--dataTag", "-t", dest="data_tag", help="Data tag for output mesh if vtk is used. Default is \"Values\"") 
    return parser.parse_args()

if __name__ == "__main__":
    main()
