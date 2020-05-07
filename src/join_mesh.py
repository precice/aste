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
    #print(vtkCells)
    points, cells, cell_types, values, offset = read_mesh(args.in_meshname, args.numparts)
    cells = vtkCells
    print(len(points))
    #print(cells)
    cellList = []
    newCellList = []
    print(offset)
    cellOrder = []

    for i in range(len(vtkCells)):
        cell_types.append(5)

    with open('cellOrder.dat','r') as f:
        for line in f:
            for char in line:
                if char in "[]]":
                    line = line.replace(char,'')

    list = line.split (",")
    for i in list:
	    cellOrder.append(int(i))

    #print "list: ", list
    #print(map)
    #print(cellOrder)
    print(cellOrder[2])
    newNumber=0
    
    for i in range(len(vtkCells)):
        for j in range(3):
            globalNumber = vtkCells[i][j]
            #print("globalNumber: ", globalNumber)
            for k in range(len(points)):
                if globalNumber == cellOrder[k*3 + 1]:
                    newNumber = cellOrder[k*3 + 2] + offset[cellOrder[k*3]] - 1
                    break
            #print("newNumber:", newNumber)
            cellList.append(newNumber)
        newCellList.append(cellList)
        cellList = []

    print(cellList)
    #tupleCellList = tuple(newCellList)
    #print(tupleCellList)
    out_meshname = args.out_meshname if args.out_meshname else args.in_meshname + ".vtk"
    write_mesh(out_meshname, points, newCellList, cell_types, values)


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
