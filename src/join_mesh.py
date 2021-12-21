#!/usr/bin/env python3
"""
Joins meshes partitioned by the ASTE mesh partitioner.

There are two possible ways of joining the meshes:
- Partition-wise (does not recover the original mesh order lacks of discarded cells)
- Recovery merge (maintain original mesh order and adds discarded cells)

Sample usage

partitioned files:
prefix_<#>.vtu

./join_mesh.py prefix -o joined_mesh.vtk

./join_mesh.py prefix -o joined_mesh.vtk -r ./path/to/recovery.json

"""

import argparse
import logging
import os
import json
import vtk


def parse_args():
    parser = argparse.ArgumentParser(description="Read a partitioned mesh and join it into a .vtk or .vtu file.")
    parser.add_argument("--mesh", "-m", dest="in_meshname", 
    help="The partitioned mesh prefix used as input (only VTU format is accepted) (Looking for <prefix>_<#filerank>.vtu) ")
    parser.add_argument("--output", "-o", dest="out_meshname", 
    help="The output mesh. Can be VTK or VTU format. If it is not given <inputmesh>_joined.vtk will be used.")
    parser.add_argument("-r", "--recovery", dest="recovery",
                        help="The path to the recovery file to fully recover it's state.")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int,
                        help="The number of parts to read from the input mesh. By default the entire mesh is read.")
    parser.add_argument("--directory", "-dir", dest="directory", default=None,
                        help="Directory for output files (optional)")
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the log level. Default is INFO")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + "_joined.vtk"
    joined_mesh = read_meshes(args.in_meshname, args.numparts, args.recovery)
    write_mesh(joined_mesh, out_meshname, args.directory)


def read_meshes(prefix: str, partitions=None, recoveryPath=None):
    """
    Reads meshes with given prefix.
    """
    if not partitions:
        partitions = count_partitions(prefix)
        logging.debug("Detected " + str(partitions) + " partitions with prefix " + prefix)
    if partitions == 0:
        raise Exception("No partitions found")

    if recoveryPath is None:
        logging.info("No recovery data found. Meshes will be joined partition-wise")
        return join_mesh_partitionwise(prefix, partitions)
    else:
        logging.info("Recovery data found. Full recovery will be executed")
        return join_mesh_recovery(prefix, partitions, recoveryPath)


def join_mesh_partitionwise(prefix: str, partitions: int):
    """
    Partition-wise load and append.
    Does not recover missing cells.
    Cells and points may be scrambled wrt original mesh.
    """

    logging.info("Starting partition-wise mesh merge")
    joined_mesh = vtk.vtkUnstructuredGrid()
    joined_points = vtk.vtkPoints()
    joined_data_arrays = None
    joined_cells = vtk.vtkCellArray()
    joined_cell_types = []
    offset = 0

    for i in range(partitions):
        fname = prefix + "_" + str(i) + ".vtu"
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(fname)
        reader.Update()
        part_mesh = reader.GetOutput()

        logging.debug("File {} contains {} points".format(fname, part_mesh.GetNumberOfPoints()))
        for i in range(part_mesh.GetNumberOfPoints()):
            joined_points.InsertNextPoint(part_mesh.GetPoint(i))

        part_point_data = part_mesh.GetPointData()
        num_arrays = part_point_data.GetNumberOfArrays()

        if joined_data_arrays is None:
            joined_data_arrays = []
            for j in range(num_arrays):
                newArr = vtk.vtkDoubleArray()
                newArr.SetName(part_point_data.GetArrayName(j))
                joined_data_arrays.append(newArr)

        for j in range(num_arrays):
            array_name = part_point_data.GetArrayName(j)
            logging.debug("Merging from file {} dataname {}".format(fname, array_name))
            array_data = part_point_data.GetArray(array_name)
            join_arr = joined_data_arrays[j]
            join_arr.SetNumberOfComponents(array_data.GetNumberOfComponents())
            join_arr.InsertTuples(join_arr.GetNumberOfTuples(), array_data.GetNumberOfTuples(), 0, array_data)

        for i in range(part_mesh.GetNumberOfCells()):
            cell = part_mesh.GetCell(i)
            vtkCell = vtk.vtkGenericCell()
            vtkCell.SetCellType(cell.GetCellType())
            idList = vtk.vtkIdList()
            for j in range(cell.GetNumberOfPoints()):
                idList.InsertNextId(cell.GetPointId(j) + offset)
            vtkCell.SetPointIds(idList)
            joined_cell_types.append(cell.GetCellType())
            joined_cells.InsertNextCell(vtkCell)

        offset += part_mesh.GetNumberOfPoints()

    if len(joined_cell_types) != 0:
        joined_mesh.SetCells(joined_cell_types, joined_cells)
    joined_mesh.SetPoints(joined_points)
    for data_array in joined_data_arrays:
        joined_mesh.GetPointData().AddArray(data_array)

    return joined_mesh


def join_mesh_recovery(prefix: str, partitions: int, recoveryPath: str):
    """
    Partition merge with full recovery

    This recovers the original mesh.
    """
    logging.info("Starting full mesh recovery")
    recovery = json.load(open(recoveryPath, "r"))
    cells = recovery["cells"]
    size = recovery["size"]
    cell_types = recovery["cell_types"]

    logging.debug("Original Mesh contains {} points".format(size))
    logging.debug("{} Cells discarded during partitioning".format(len(cells)))

    # Initialize Joined Mesh
    joined_mesh = vtk.vtkUnstructuredGrid()
    joined_points = vtk.vtkPoints()
    joined_points.SetNumberOfPoints(size)
    joined_data_arrays = None
    joined_cells = vtk.vtkCellArray()
    joined_cell_types = []

    for i in range(partitions):
        global_ids = []

        fname = prefix + "_" + str(i) + ".vtu"
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(fname)
        reader.Update()
        part_mesh = reader.GetOutput()
        part_point_data = part_mesh.GetPointData()
        num_arrays = part_point_data.GetNumberOfArrays()

        # Prepare DataArrays
        if joined_data_arrays is None:
            joined_data_arrays = []
            for j in range(num_arrays):
                newArr = vtk.vtkDoubleArray()
                newArr.SetName(part_point_data.GetArrayName(j))
                newArr.SetNumberOfTuples(size)
                joined_data_arrays.append(newArr)

        # Extract Global IDs
        array_data = part_point_data.GetArray("GlobalIDs")
        # Check if GlobalIDs exist if not do partition-wise merge
        if array_data is None:
            logging.warning("GlobalIDs were not found, a recovery merge is not possible.")
            return join_mesh_partitionwise(prefix, partitions)

        for k in range(array_data.GetNumberOfTuples()):
            global_ids.append(array_data.GetTuple(k))
        logging.debug("File {} contains {} points".format(fname, part_mesh.GetNumberOfPoints()))
        for i in range(part_mesh.GetNumberOfPoints()):
            joined_points.SetPoint(int(global_ids[i][0]), part_mesh.GetPoint(i))

        # Append Point Data to Original Locations
        for j in range(num_arrays):
            array_name = part_point_data.GetArrayName(j)
            logging.debug("Merging from file {} dataname {}".format(fname, array_name))
            array_data = part_point_data.GetArray(array_name)
            join_arr = joined_data_arrays[j]
            join_arr.SetNumberOfComponents(array_data.GetNumberOfComponents())
            join_arr.SetNumberOfTuples(size)
            for k in range(array_data.GetNumberOfTuples()):
                join_arr.SetTuple(int(global_ids[k][0]), array_data.GetTuple(k))

        # Append Cells
        for i in range(part_mesh.GetNumberOfCells()):
            cell = part_mesh.GetCell(i)
            vtkCell = vtk.vtkGenericCell()
            vtkCell.SetCellType(cell.GetCellType())
            idList = vtk.vtkIdList()
            for j in range(cell.GetNumberOfPoints()):
                idList.InsertNextId(int(global_ids[cell.GetPointId(j)][0]))
            vtkCell.SetPointIds(idList)
            joined_cell_types.append(cell.GetCellType())
            joined_cells.InsertNextCell(vtkCell)

    # Append Recovery Cells
        for cell, cell_type in zip(cells, cell_types):
            vtkCell = vtk.vtkGenericCell()
            vtkCell.SetCellType(cell_type)
            idList = vtk.vtkIdList()
            for pointid in cell:
                idList.InsertNextId(pointid)
            vtkCell.SetPointIds(idList)
            joined_cell_types.append(cell_type)
            joined_cells.InsertNextCell(vtkCell)

    # Set Points, Cells, Data on Grid
    if len(joined_cell_types) != 0:
        joined_mesh.SetCells(joined_cell_types, joined_cells)
    joined_mesh.SetPoints(joined_points)
    for data_array in joined_data_arrays:
        joined_mesh.GetPointData().AddArray(data_array)

    return joined_mesh


def count_partitions(prefix: str) -> int:
    """Count how many partitions available with given prefix

    Args:
        prefix (str): prefix of mesh

    Returns:
        int: number of partitions
    """
    detected = 0
    while True:
        partitionFile = prefix + "_" + str(detected) + ".vtu"
        if (not os.path.isfile(partitionFile)):
            break
        detected += 1
    return detected


def write_mesh(meshfile, filename, directory=None):

    filename = os.path.basename(os.path.normpath(filename))
    if directory:
        directory = os.path.abspath(directory)
        os.makedirs(directory, exist_ok=True)
        filename = os.path.join(directory, filename)

    extension = os.path.splitext(filename)[1]
    if (extension == ".vtk"):  # VTK Legacy format
        writer = vtk.vtkUnstructuredGridWriter()
    elif (extension == ".vtu"):  # VTK XML Unstructured Grid format
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Unkown File extension: " + extension)
    writer.SetFileName(filename)
    writer.SetInputData(meshfile)
    writer.Write()


if __name__ == "__main__":
    main()
