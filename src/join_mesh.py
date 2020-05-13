#!/usr/bin/env python3
import argparse, math
import logging
import os
import re
import numpy as np
from ctypes import *
import mesh_io
import partition_mesh
from mesh_io import read_txt, write_mesh


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    in_vtkname = args.in_vtkname if args.in_vtkname else args.in_meshname + ".vtk"
    vtkPoints,vtkCells, vtkCellTypes,vtkValues = mesh_io.read_mesh(in_vtkname, args.numparts)
    points, cells, cell_types, values, offset = read_mesh(args.in_meshname, args.numparts)
    #cells = vtkCells
    cellList = []
    combinedCellList = []
    partitionNumbering = []
    globalIDNumbering = []
    localIDNumbering = []

    for i in range(len(vtkCells)):
        cell_types.append(5)

    with open('partitionOrder.dat','r') as pOrder:
        for line in pOrder:
            for char in line:
                if char in "[]":
                    line = line.replace(char,'')

    list = line.split (",")
    for i in list:
	    partitionNumbering.append(int(i))

    with open('globalOrder.dat','r') as gOrder:
        for line in gOrder:
            for char in line:
                if char in "[]":
                    line = line.replace(char,'')

    list = line.split (",")
    for i in list:
	    globalIDNumbering.append(int(i))

    with open('localOrder.dat','r') as iOrder:
        for line in iOrder:
            for char in line:
                if char in "[]":
                    line = line.replace(char,'')

    list = line.split (",")
    for i in list:
	    localIDNumbering.append(int(i))
    
    localIdNumber=0
    for i in range(len(vtkCells)):
        for j in range(3):
            globalNumber = vtkCells[i][j]
            localIdNumber = localIDNumbering[globalNumber] + offset[partitionNumbering[globalNumber]] - 1
            cellList.append(localIdNumber)
        combinedCellList.append(cellList)
        cellList = []

    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"
    write_mesh(out_meshname, points, combinedCellList, cell_types, values)


def read_mesh(dirname, length = None):
    """
    Reads a mesh from the given directory. If length is given, only the first length parts are read, 
    else length is inferred from the files. 
    """

    if not length:
        length = 0
        while os.path.isfile(os.path.join(dirname, str(length))):
            length += 1
    dirname = os.path.abspath(dirname)
    if not os.path.exists(dirname):
        raise Exception("Directory not found")
    all_points = []
    all_values = []
    all_cells = []
    all_cell_types = []
    all_offset = []
    for i in range(length):
        points, cells, cell_types, values = read_txt(os.path.join(dirname, str(i)))
        offset = len(all_points)
        all_points += points
        all_values += values
        all_offset.append(offset)
        all_cells += [
            tuple(map(lambda idx: idx+offset, cell))
            for cell in cells
        ]
        all_cell_types += cell_types
        #all_cells.append(offset)
        #all_cell_types.append(offset)
        #    tuple(map(lambda idx: idx+offset, cell))
        #    for cell in cells
        #all_cell_types += cell_types
    return all_points, all_cells, all_cell_types, all_values, all_offset


def parse_args():
    parser = argparse.ArgumentParser(description="""Read a partitioned mesh 
            and join it into a .vtk or .txt file.""")
    parser.add_argument("in_meshname", metavar="inputmesh", help="The partitioned mesh used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh. Can be vtk or txt.")
    parser.add_argument("--in", "-i", dest="in_vtkname", help="The VTK filename for building output VTK")
    parser.add_argument("--numparts", "-n", dest="numparts", type=int, 
            help="The number of parts to read from the input mesh. By default the entire mesh is read.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the log level. Default is INFO")
    return parser.parse_args()


if __name__ == "__main__":
    main()
