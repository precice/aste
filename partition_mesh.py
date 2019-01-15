#!/usr/bin/python3
import vtk
import os
import numpy as np
from ctypes import *
from tqdm import tqdm
import argparse
class Mesh:
    """
    A Mesh consists of:
        - Points: A list of tuples of floats representing coordinates of points
        - Cells: A list of tuples of ints representing mesh elements
        - Pointdata: A list of floats representing data values at the respective point
    """
    def __init__(self, vtkmesh = None, tag = None):
        """
        This constructor can be called without arguments or can be given a vtk.vtkDataSet
        with an optional value tag, if values are defined on the points.
        """
        self.cells = []
        self.points = []
        self.pointdata = []
        if vtkmesh:
            for i in range(vtkmesh.GetNumberOfCells()):
                cell = vtkmesh.GetCell(i)
                entry = ()
                for j in range(cell.GetNumberOfPoints()):
                    entry += (cell.GetPointId(j),)
                self.cells.append(entry)
            self.points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
            fieldData = vtkmesh.GetPointData().GetScalars()
            if fieldData:
                for i in range(vtkmesh.GetNumberOfPoints()):
                    self.pointdata.append(fieldData.GetTuple(i))

def main():
    args = parse_args()
    print("Reading mesh...")
    mesh = read_mesh(args.in_meshname)
    print("Done.")
    numparts = args.numparts if args.numparts else 1
    if numparts > 1:
        print("Partitioning mesh...")
        part = partition(mesh, numparts)
        print("Done.")
    else:
        part = [0] *  len(mesh.points)
    meshes = generate_meshes(mesh, part, numparts)
    if not args.out_meshname:
        out_meshname = args.in_meshname[:-4]
        print("No --out given. Setting output to: " + out_meshname)
    else:
        out_meshname = args.out_meshname
    print("Writing mesh...")
    write_meshes(meshes, out_meshname)
    print("Done.")

def read_mesh(filename):
    """
    Reads a mesh from the given filename. For vtk meshes a tag for the data values can be given. 
    """
    if filename[-4:] == ".vtk":
        result = []
        reader = vtk.vtkDataSetReader()
        reader.SetFileName(filename)
        reader.Update()
        output = reader.GetOutput()
        return Mesh(output)
    elif filename[-4:] == ".txt":
        mesh = Mesh()
        with open(filename, "r") as fh:
            for line in tqdm(fh, "Reading lines"):
                point = ()
                parts = line.split(" ")
                for i in range(3):
                    point += (float(parts[i]),)
                mesh.points.append(point)
                if len(parts) > 3:
                    mesh.pointdata.append(tuple(parts[3:]))
        return mesh
    raise Exception("Invalid file extension.")

def partition(mesh, numparts):
    """
    Partitions a mesh using METIS. This does not call METIS directly, but instead uses a small C++ Wrapper libmetisAPI.so for convenience. This shared library must be provided if this function should be called.
    """
    if not mesh.cells:
        print("No topology information given. This will yield arbitrary partitions")
    cellPtr = [0]
    cellData = []
    for i in range(len(mesh.cells)):
        cell = mesh.cells[i]
        cellData += list(cell)
        cellPtr.append(cellPtr[-1] + len(cell))
    libmetis = cdll.LoadLibrary(os.path.abspath("libmetisAPI.so"))
    idx_t = c_int if libmetis.typewidth() == 32 else c_longlong
    cell_count = idx_t(len(mesh.cells))
    point_count = idx_t(len(mesh.points))
    num_parts = idx_t(numparts)
    partition = (idx_t * len(mesh.points))()
    cell_ptr = (idx_t * len(cellPtr))(*cellPtr)
    cell_data = (idx_t * len(cellData))(*cellData)
    libmetis.partitionMetis(cell_count, point_count, cell_ptr, cell_data, num_parts, partition)
    arr = np.ctypeslib.as_array(partition)
    return arr

def generate_meshes(mesh, part, numparts):
    """
    Partitions a mesh into many meshes when given a partition and a mesh.
    """
    meshes = [[] for _ in range(numparts)]
    for i in range(len(mesh.points)):
        selected = meshes[part[i]]
        entry = ()
        entry += mesh.points[i]
        if mesh.pointdata:
            entry += mesh.pointdata[i]
        selected.append(entry)
    return meshes

def write_meshes(meshes, dirname):
    """
    Writes meshes to given directory.
    """
    dirname = os.path.abspath(dirname)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    for i in range(len(meshes)):
        mesh = meshes[i]
        with open(dirname + "/" + str(i), "w+") as file:
            for entry in mesh:
                file.write(" ".join(map(str, entry)) + "\n")
def parse_args():
    parser = argparse.ArgumentParser(description="Read vtk meshes, partition them and write them out in internal format")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The vtk mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh directory name")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, help="The number of parts to split into")
    parser.add_argument("--dataTag", "-t", dest="data_tag", help="Data tag for vtk mesh") 
    return parser.parse_args()

if __name__ == "__main__":
    main()
