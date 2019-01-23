#!/usr/bin/env python3
import logging
import os
import numpy as np
from ctypes import *
import argparse
import mesh_io

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    mesh = read_mesh(args.in_meshname)
    if args.algorithm == "meshfree" or (not mesh.cells and not args.algorithm):
        algorithm = "meshfree"
    else:
        algorithm = "topology"
    if args.numparts > 1:
        part = partition(mesh, args.numparts, algorithm)
    else:
        part = [0] *  len(mesh.points)
    meshes = apply_partition(mesh, part, args.numparts)
    if not args.out_meshname:
        out_meshname = args.in_meshname[:-4]
        logging.info("No --out given. Setting output to: " + out_meshname)
    else:
        out_meshname = args.out_meshname
    write_meshes(meshes, out_meshname)

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

def read_mesh(filename):
    points, cells, _, pointdata = mesh_io.read_mesh(filename)
    return Mesh(points, cells, pointdata)
def partition(mesh, numparts, algorithm):
    """
    Partitions a mesh using METIS or kmeans. This does not call METIS directly, but instead uses a small C++ Wrapper libmetisAPI.so for convenience. This shared library must be provided if this function should be called.
    """
    if algorithm == "meshfree":
        return partition_kmeans(mesh, numparts)
    else:
        return partition_metis(mesh, numparts)

def partition_kmeans(mesh, numparts):
    points = np.copy(mesh.points)
    points = reduce_dimension(points)
    from scipy.cluster.vq import kmeans2
    _, label = kmeans2(points, numparts)
    return label

def reduce_dimension(mesh):
    testP = mesh[0]
    dead_dims = np.argwhere(np.abs(np.array(testP)) < 1e-9)
    for point in mesh:
        current_dead_dims = np.argwhere(np.abs(np.array(point)) < 1e-9)
        dead_dims = np.intersect1d(dead_dims, current_dead_dims)
        if len(dead_dims) == 0:
            return mesh
    mesh = np.array(mesh)
    full = np.array([0,1,2])
    mask = np.setdiff1d(full, dead_dims)
    return mesh[:,mask]


def reduce_dimension_WIP(mesh):
    pA, pB, pC = mesh[:3]
    pA = np.array(pA)
    AB = pB - pA
    AC = pC - pA
    n = np.cross(AB, AC)
    # Every point x in the plane must fulfill (x - pA) * n = 0
    for x in mesh:
        if not np.dot(x - pA, n) == 0:
            break
    else: # All Points within plane
        # Transform mesh so all points have form (0, y, z)
        pass # TODO: This is WIP

def partition_metis(mesh, numparts):
    """
    Partitions a mesh using METIS. This does not call METIS directly, but instead uses a small C++ Wrapper libmetisAPI.so for convenience. This shared library must be provided if this function should be called.
    """
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
    parser.add_argument("--numparts", "-n", dest="numparts", default=1, type=int, help="The number of parts to split into")
    parser.add_argument("--algorithm", "-a", dest="algorithm", choices=["meshfree", "topology"], help="Change the algorithm used for determining a partition. A meshfree algorithm works on arbitrary meshes without needing topological information. A topology-based algorithm needs topology information and is therefore useless on point clouds")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()

if __name__ == "__main__":
    main()
