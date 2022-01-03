#!/usr/bin/env python3
import argparse
import logging
import math
import os
from typing import List
import numpy as np
import shutil
from ctypes import *
import json


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    mesh_name = args.in_meshname
    assert os.path.isfile(mesh_name), ("Invalid filename: " + mesh_name)

    algorithm = args.algorithm
    if not algorithm:
        logging.info("No algorithm given. Defaulting to \"meshfree\"")
        algorithm = "meshfree"
    mesh = read_mesh(mesh_name)
    if args.numparts > 1:
        part = partition(mesh, args.numparts, algorithm)
    else:
        if args.directory:
            # Get the absolute directory where we want to store the mesh
            directory = os.path.abspath(args.directory)
            os.makedirs(directory, exist_ok=True)
            out_meshname = os.path.join(directory, args.out_meshname)
        else:
            out_meshname = args.out_meshname
        extension = os.path.splitext(mesh_name)[1]
        if extension == ".vtk":
            shutil.copy(mesh_name, out_meshname + ".vtk")
            return
        elif extension == ".vtu":
            vtu2vtk(mesh_name, out_meshname)
            return
        else:
            print("Unkown input file extension please check your input file.")
            os.exit()

    logging.info("Processing mesh " + mesh_name)
    meshes, recoveryInfo = apply_partition(mesh, part, args.numparts)
    logging.info("Writing output to: " + args.out_meshname)
    write_meshes(meshes, recoveryInfo, args.out_meshname, mesh.vtk_dataset, args.directory)


class Mesh:
    """
    A Mesh consists of:
        - Points: A list of tuples of floats representing coordinates of points
        - Cells: A list of tuples of ints representing mesh elements
        - data_index: A list ints representing indexes of Points/Data in original mesh
        - vtk_Dataset: VTK Unstructured Grid Object.
    """

    def __init__(self, points=None, cells=None, cell_types=None, vtk_dataset=None, data_index=None):
        if points is not None:
            self.points = points
        else:
            self.points = []
        if cells is not None:
            assert(cell_types is not None)
            self.cells = cells
            self.cell_types = cell_types
        else:
            self.cells = []
            self.cell_types = []

        if data_index is not None:
            self.data_index = data_index
        else:
            self.data_index = []

        self.vtk_dataset = vtk_dataset

    def __str__(self):
        return "Mesh with {} Points and {} Cells ({} Cell Types)".format(
            len(self.points), len(self.cells), len(self.cell_types))


def partition(mesh: Mesh, numparts: int, algorithm):
    """
    Partitions a mesh using METIS or kmeans. This does not call METIS directly,
    but instead uses a small C++ Wrapper libmetisAPI.so for convenience.
    This shared library must be provided if this function should be called.
    """
    if algorithm == "meshfree":
        return partition_kmeans(mesh, numparts)
    elif algorithm == "topology":
        return partition_metis(mesh, numparts)
    elif algorithm == "uniform":
        labels = partition_uniform(mesh, numparts)
        if labels is None:
            return partition(mesh, numparts, "meshfree")
        return labels


def partition_kmeans(mesh: Mesh, numparts: int):
    """ Partitions a mesh using k-means. This is a meshfree algorithm and requires scipy"""
    from scipy.cluster.vq import kmeans2
    points = np.copy(mesh.points)
    points = reduce_dimension(points)
    _, label = kmeans2(points, numparts)
    return label


def reduce_dimension_simple(mesh: Mesh):
    """
    A simple, efficient algorithm for a dimension reduction for a mesh
    with one or more "dead dimensions"
    """
    testP = mesh[0]
    dead_dims = np.argwhere(np.abs(np.array(testP)) < 1e-9)
    for point in mesh:
        current_dead_dims = np.argwhere(np.abs(np.array(point)) < 1e-9)
        dead_dims = np.intersect1d(dead_dims, current_dead_dims)
        if len(dead_dims) == 0:
            return mesh
    mesh = np.array(mesh)
    full = np.array([0, 1, 2])
    mask = np.setdiff1d(full, dead_dims)
    return mesh[:, mask]


def reduce_dimension(mesh: Mesh):
    """
    This function gets a list of points in 3d and if all of them are within one plane it
    returns a list of 2d points in the plane, else the unmodified list is returned.
    """
    pA, pB = mesh[:2]
    pC = mesh[-1]
    pA = np.array(pA)
    AB = pB - pA
    AC = pC - pA
    n = np.cross(AB, AC)
    # Every point x in the plane must fulfill (x - pA) * n = 0
    for x in mesh:
        if not np.dot(x - pA, n) == 0:
            return mesh
    else:  # All Points within plane
        # Transform mesh so all points have form (0, y, z)
        # Compute Euler-Rodrigues rotation matrix
        n /= np.linalg.norm(n)  # Normalize
        zUnit = np.array((0, 0, 1))
        phi = math.acos(np.dot(n, zUnit))
        logging.info("Rotating mesh with phi = " + str(360 * phi / (2 * math.pi)) + " degrees.")
        axis = np.cross(n, zUnit)
        axis /= np.linalg.norm(axis)
        a = math.cos(phi / 2)
        b = math.sin(phi / 2) * axis[0]
        c = math.sin(phi / 2) * axis[1]
        d = math.sin(phi / 2) * axis[2]
        rotMat = np.array((
            (a**2 + b**2 - c**2 - d**2, 2 * (b * c - a * d), 2 * (b * d + a * c)),
            (2 * (b * c + a * d), a**2 + c**2 - b**2 - d**2, 2 * (c * d - a * b)),
            (2 * (b * d - a * c), 2 * (c * d + a * b), a**2 + d**2 - b**2 - c**2)))
        for i, x in enumerate(mesh):  # Translate & Rotate
            x -= pA
            x = x @ rotMat
            mesh[i] = x
        return mesh[:, :-1]


def partition_metis(mesh: Mesh, numparts: int):
    """
    Partitions a mesh using METIS. This does not call METIS directly,
    but instead uses a small C++ Wrapper libmetisAPI.so for convenience.
    This shared library must be provided if this function should be called.
    """
    cellPtr = [0]
    cellData = []
    if len(mesh.cells) == 0:
        logging.warning("No topology information provided. Partitioning with metis will likely provide bad partition")
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
    return np.ctypeslib.as_array(partition)


def partition_uniform(mesh: Mesh, numparts: int):
    """
    Partitions a mesh assuming it is uniform. It must be two-dimensional
    but is allowed to be layed out anyhow in three dimensions.
    """
    mesh = mesh.points[:]
    mesh = reduce_dimension(np.array(mesh))
    if len(mesh[0]) == 3:
        logging.warning("Mesh is not uniform. Falling back to meshfree method")
        return None
    min_point = np.amin(mesh, 0)
    max_point = np.amax(mesh, 0)
    big_dim = 0 if max_point[0] - min_point[0] >= max_point[1] - min_point[1] else 1
    small_dim = 1 - big_dim

    def prime_factors(n):
        """ Straight from SO"""
        i = 2
        factors = []
        while i * i <= n:
            if n % i:
                i += 1
            else:
                n //= i
                factors.append(i)
        if n > 1:
            factors.append(n)
        return factors

    def greedy_choose(factors):
        """ Greedily choose "best" divisors"""
        small = big = 1
        for factor in reversed(factors):
            if big <= small:
                big *= factor
            else:
                small *= factor
        return small, big

    small, big = greedy_choose(prime_factors(numparts))
    small_interval = (max_point[small_dim] - min_point[small_dim]) / small
    big_interval = (max_point[big_dim] - min_point[big_dim]) / big
    labels = []
    logging.info("Uniform partioning of mesh size {} into {} x {} partitions.".format(
        len(mesh), small, big))
    for point in mesh:
        small_offset = point[small_dim] - min_point[small_dim]
        small_index = int(small_offset / small_interval)
        small_index = min(small_index, small - 1)
        big_offset = point[big_dim] - min_point[big_dim]
        big_index = int(big_offset / big_interval)
        big_index = min(big_index, big - 1)
        partition_num = small_index * big + big_index
        labels.append(partition_num)
    return labels


def apply_partition(orig_mesh: Mesh, part, numparts: int):
    """
    Partitions a mesh into many meshes when given a partition and a mesh.
    """
    meshes = [Mesh() for _ in range(numparts)]
    mapping = {}  # Maps global index to partition and local index
    for i, point in enumerate(orig_mesh.points):
        partition = part[i]
        selected = meshes[partition]
        mapping[i] = (partition, len(selected.points))
        selected.points.append(point)
        selected.data_index.append(i)

    assert(len(mapping) == len(orig_mesh.points))
    assert(len(orig_mesh.cells) == len(orig_mesh.cell_types))
    # Save discarded cells and their types to allow recovery
    discardedCells = []
    discardedCellTypes = []
    for cell, type in zip(orig_mesh.cells, orig_mesh.cell_types):
        partitions = list(map(lambda idx: mapping[idx][0], cell))
        if len(set(partitions)) == 1:
            meshes[partitions[0]].cells.append(tuple([mapping[gidx][1] for gidx in cell]))
            meshes[partitions[0]].cell_types.append(type)
        else:
            discardedCells.append(list(cell))
            discardedCellTypes.append(type)

    recoveryInfo = {
        "size": len(orig_mesh.points),
        "cells": discardedCells,
        "cell_types": discardedCellTypes
    }

    return meshes, recoveryInfo


def read_mesh(filename: str) -> Mesh:
    import vtk
    extension = os.path.splitext(filename)[1]
    if (extension == ".vtu"):
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif (extension == ".vtk"):
        reader = vtk.vtkUnstructuredGridReader()
    else:
        print("Unkown input file extension please check your input file.")
        os.exit()
    reader.SetFileName(filename)
    reader.Update()
    vtkmesh = reader.GetOutput()
    points = []
    cells = []
    cell_types = []
    points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
    for i in range(vtkmesh.GetNumberOfCells()):
        cell = vtkmesh.GetCell(i)
        cell_type = cell.GetCellType()
        if cell_type not in [vtk.VTK_LINE, vtk.VTK_TRIANGLE, vtk.VTK_QUAD]:
            continue
        cell_types.append(cell_type)
        entry = ()
        for j in range(cell.GetNumberOfPoints()):
            entry += (cell.GetPointId(j), )
        cells.append(entry)

    assert (len(cell_types) in [0, len(cells)])
    return Mesh(points, cells, cell_types, vtkmesh)


def write_mesh(filename: str, points: List, data_index: List, cells=None, cell_types=None, orig_mesh=None) -> None:
    if (cell_types is not None):
        assert (len(cell_types) in [0, len(cells)])
    assert (len(points) == len(data_index))
    import vtk

    vtkGrid = vtk.vtkUnstructuredGrid()
    vtkpoints = vtk.vtkPoints()
    vtkpoints.SetNumberOfPoints(len(points))
    for id, point in enumerate(points):
        vtkpoints.SetPoint(id, point)
    vtkGrid.SetPoints(vtkpoints)

    if cells:
        cellArray = vtk.vtkCellArray()
        for i, cell in enumerate(cells):
            vtkCell = vtk.vtkGenericCell()
            vtkCell.SetCellType(cell_types[i])
            idList = vtk.vtkIdList()
            for cellid in cell:
                idList.InsertNextId(cellid)
            vtkCell.SetPointIds(idList)
            cellArray.InsertNextCell(vtkCell)
        vtkGrid.SetCells(cell_types, cellArray)

    # Add GlobalIDs as a PointData
    globalIdArr = vtk.vtkDoubleArray()
    globalIdArr.SetNumberOfComponents(1)
    globalIdArr.SetName("GlobalIDs")
    for j in data_index:
        globalIdArr.InsertNextTuple1(j)
    vtkGrid.GetPointData().AddArray(globalIdArr)

    if orig_mesh is not None:  # Take PointDatas
        point_data = orig_mesh.GetPointData()
        # Iterate over PointData
        for i in range(point_data.GetNumberOfArrays()):
            array_name = point_data.GetArrayName(i)
            oldArr = point_data.GetAbstractArray(array_name)
            newArr = vtk.vtkDoubleArray()
            num_comp = oldArr.GetNumberOfComponents()
            newArr.SetNumberOfComponents(num_comp)
            newArr.SetName(array_name)
            if num_comp == 1:
                for j in data_index:
                    data = oldArr.GetTuple1(j)
                    newArr.InsertNextTuple1(data)
            elif num_comp == 2:
                for j in data_index:
                    data = oldArr.GetTuple2(j)
                    newArr.InsertNextTuple2(data[0], data[1])
            elif num_comp == 3:
                for j in data_index:
                    data = oldArr.GetTuple3(j)
                    newArr.InsertNextTuple3(data[0], data[1], data[2])
            else:
                logging.warning("Skipped data {} check dimension of data".format(array_name))
            vtkGrid.GetPointData().AddArray(newArr)

    extension = os.path.splitext(filename)[1]
    if (extension == ".vtk"):  # VTK Legacy format
        writer = vtk.vtkUnstructuredGridWriter()
        writer.SetFileTypeToBinary()
    elif (extension == ".vtu"):  # VTK XML Unstructured Grid format
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Unkown File extension: " + extension)
    writer.SetFileName(filename)
    writer.SetInputData(vtkGrid)
    writer.Write()
    return


def write_meshes(meshes, recoveryInfo, meshname: str, orig_mesh, directory=None) -> None:
    """
    Writes meshes to given directory.
    """

    recoveryName = os.path.basename(os.path.normpath('recovery.json'))
    # Strip off the mesh-prefix for the directory creation
    mesh_prefix = os.path.basename(os.path.normpath(meshname))
    if directory:
        # Get the absolute directory where we want to store the mesh
        directory = os.path.abspath(directory)
        recoveryName = os.path.join(directory, 'recovery.json')
        os.makedirs(directory, exist_ok=True)

    for i in range(len(meshes)):
        mesh = meshes[i]
        if directory:
            write_mesh(os.path.join(directory, mesh_prefix) + "_" + str(i) + ".vtu", mesh.points, mesh.data_index,
                       mesh.cells, mesh.cell_types, orig_mesh)
        else:
            write_mesh(mesh_prefix + "_" + str(i) + ".vtu", mesh.points, mesh.data_index, mesh.cells,
                       mesh.cell_types, orig_mesh)
    json.dump(recoveryInfo, open(recoveryName, "w"))
    return


def parse_args():
    parser = argparse.ArgumentParser(description="Read meshes, partition them and write them out in VTU format.")
    parser.add_argument("--mesh", "-m", required=True, dest="in_meshname", help="The mesh used as input")
    parser.add_argument("--output", "-o", dest="out_meshname", default="partitioned_mesh",
                        help="The output mesh name.")
    parser.add_argument("--directory", "-dir", dest="directory", default=None,
                        help="Directory for output files (optional)")
    parser.add_argument("--numparts", "-n", dest="numparts", default=1, type=int,
                        help="The number of parts to split into")
    parser.add_argument("--algorithm", "-a", dest="algorithm", choices=["meshfree", "topology", "uniform"],
                        help="""Change the algorithm used for determining a partition.
            A meshfree algorithm works on arbitrary meshes without needing topological information.
            A topology-based algorithm needs topology information
            and is therefore useless on point clouds.
            A uniform algorithm will assume a uniform 2d mesh layed out somehow in 3d and partition accordingly.""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the log level. Default is INFO")
    return parser.parse_args()


def vtu2vtk(inmesh, outmesh):
    import vtk
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(inmesh)
    reader.Update()
    mesh = reader.GetOutput()
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(outmesh + ".vtk")
    writer.SetInputData(mesh)
    writer.SetFileTypeToBinary()
    writer.Write()
    return


if __name__ == "__main__":
    main()
