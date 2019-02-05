""" 
Mesh I/O utility script. One can read meshes from .vtk, .txt, .vtu, .vtp,... files
 and save to .txt, .vtk and .vtu
"""

import os
import vtk


def read_mesh(filename):
    """
    Returns Mesh Points, Mesh Cells, Mesh Celltypes, 
    Mesh Pointdata in this order
    """
    if os.path.splitext(filename)[1] == ".txt":
        return read_txt(filename)
    else:
        return read_vtk(filename)

    
def write_mesh(filename, points, cells = None, cell_types = None, values = None):
    if os.path.splitext(filename)[1] == ".txt":
        if cells is not None and len(cells) > 0:
            logging.warning("Saving as .txt discards topology")
        return write_txt(filename, points, values) # TODO: Warn on cells
    else:
        return write_vtk(filename, points, cells, cell_types, values)

    
def read_vtk(filename):
    vtkmesh = read_dataset(filename)
    points = []
    cells = []
    pointdata = []
    cell_types = []
    points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
    for i in range(vtkmesh.GetNumberOfCells()):
        cell = vtkmesh.GetCell(i)
        cell_types.append(cell.GetCellType())
        entry = ()
        for j in range(cell.GetNumberOfPoints()):
            entry += (cell.GetPointId(j),)
        cells.append(entry)
    fieldData = vtkmesh.GetPointData().GetScalars()
    if fieldData:
        for i in range(vtkmesh.GetNumberOfPoints()):
            pointdata.append(fieldData.GetTuple1(i))
    return points, cells, cell_types, pointdata


def read_dataset(filename):
    extension = os.path.splitext(filename)[1]
    if (extension == ".vtk"): # VTK Legacy format
        reader = vtk.vtkDataSetReader()
    elif (extension == ".vtp"): # VTK XML Poly format
        reader = vtk.vtkXMLPolyDataReader()
    elif (extension == ".vtu"): # VTK XML Unstructured format
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif (extension == ".stl"): # Stereolithography format
        reader = vtk.vtkSTLReader()
    elif (extension == ".ply"): # Stanford triangle format
        reader = vtk.vtkPLYReader()
    elif (extension == ".obj"): # Wavefront OBJ format
        reader = vtk.vtkOBJReader()
    else:
        raise Exception("Unkown File extension: " + extension)
    reader.SetFileName(filename)
    reader.Update()
    return reader.GetOutput()


def read_txt(filename):
    points = []
    pointdata = []
    with open(filename, "r") as fh:
        for line in fh:
            point = ()
            parts = line.split(" ")
            for i in range(3):
                point += (float(parts[i]),)
            points.append(point)
            if len(parts) > 3:
                pointdata.append(float(parts[3]))
    return points, [], [], pointdata


def write_vtk(filename, points, cells = None, cell_types = None, pointdata = None):
    data = vtk.vtkUnstructuredGrid() # is also vtkDataSet
    scalars = vtk.vtkDoubleArray()
    vtkpoints = vtk.vtkPoints()
    for i, point in enumerate(points):
        vtkpoints.InsertPoint(i, point)
        if pointdata is not None and len(pointdata) > 0:
            scalars.InsertTuple1(i, pointdata[i])
    data.SetPoints(vtkpoints)
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
        data.SetCells(cell_types, cellArray)
    pointData = data.GetPointData()
    pointData.SetScalars(scalars)
    write_dataset(filename, data)

    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(filename)
    writer.SetInputData(data)
    writer.Write()

    
def write_dataset(filename, dataset):
    extension = os.path.splitext(filename)[1]
    if (extension == ".vtk"): # VTK Legacy format
        writer = vtk.vtkUnstructuredGridWriter()
    elif (extension == ".vtu"): # VTK XML Unstructured Grid format
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Unkown File extension: " + extension)
    writer.SetFileName(filename)
    writer.SetInputData(dataset)
    writer.Write()

def write_txt(filename, points, pointdata = None):
    with open(filename, "w") as fh:
        for i, point in enumerate(points):
            entry = (str(point[0]), str(point[1]), str(point[2]))
            if pointdata is not None and len(pointdata) > 0:
                entry += (str(float(pointdata[i])),)
            fh.write(" ".join(entry) + "\n")
