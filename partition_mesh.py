#!/usr/bin/env python3
import os
import numpy as np
from ctypes import *
import argparse
import mesh_io
class Mesh:
    """
    A Mesh consists of:
        - Points: A list of tuples of floats representing coordinates of points
        - Cells: A list of tuples of ints representing mesh elements
        - Pointdata: A list of floats representing data values at the respective point
    """
    def __init__(self, points = None, cells = None, pointdata = None):
        if points is not None:
            self.points = points
        else:
            self.points = []
        if cells is not None:
            self.cells = cells
        else:
            self.cells = []
        if pointdata is not None:
            self.pointdata = pointdata
        else:
            self.pointdata = []

def main():
    args = parse_args()
    mesh = read_mesh(args.in_meshname)
    numparts = args.numparts if args.numparts else 1
    if numparts > 1:
        part = partition(mesh, numparts)
    else:
        part = [0] *  len(mesh.points)
    meshes = apply_partition(mesh, part, numparts)
    if not args.out_meshname:
        out_meshname = args.in_meshname[:-4]
        print("No --out given. Setting output to: " + out_meshname)
    else:
        out_meshname = args.out_meshname
    write_meshes(meshes, out_meshname)

def read_mesh(filename):
    return Mesh(*mesh_io.read_mesh(filename))
def partition(mesh, numparts):
    """
    Partitions a mesh using METIS. This does not call METIS directly, but instead uses a small C++ Wrapper libmetisAPI.so for convenience. This shared library must be provided if this function should be called.
    """
    if True or not mesh.cells:
        return partition_kmeans(mesh, numparts)
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
def partition_kmeans(mesh, numparts):
    from scipy.cluster.vq import kmeans2
    _, label = kmeans2(mesh.points, numparts)
    return label

def apply_partition(orig_mesh, part, numparts):
    """
    Partitions a mesh into many meshes when given a partition and a mesh.
    """
    meshes = [Mesh()] * numparts
    for i in range(len(orig_mesh.points)):
        selected = meshes[part[i]]
        selected.points.append(orig_mesh.points[i])
        if orig_mesh.pointdata:
            selected.pointdata.append(orig_mesh.pointdata[i])
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
        mesh_io.write_txt(dirname + "/" + str(i), mesh.points, mesh.pointdata)
def parse_args():
    parser = argparse.ArgumentParser(description="Read vtk meshes, partition them and write them out in internal format")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The vtk mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh directory name")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, help="The number of parts to split into")
    parser.add_argument("--dataTag", "-t", dest="data_tag", help="Data tag for vtk mesh") 
    return parser.parse_args()

if __name__ == "__main__":
    main()
