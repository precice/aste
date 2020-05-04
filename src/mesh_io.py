""" 
Mesh I/O utility script. One can read meshes from .vtk, .txt, .vtu, .vtp,... files
 and save to .txt, .vtk and .vtu
"""

import os
import logging
import numpy as np


def read_mesh(filename, tag = None, datadim=1):
    """
    Returns Mesh Points, Mesh Cells, Mesh Celltypes, 
    Mesh Pointdata in this order
    """
    if os.path.splitext(filename)[1] == ".txt":
        return read_txt(filename)
    else:
        return read_vtk(filename, tag, datadim)

    
def write_mesh(filename, points, cells = None, cell_types = None, values = None, datadim=1):
    if os.path.splitext(filename)[1] == ".txt":
        return write_txt(filename, points, cells, values)
    else:
        return write_vtk(filename, points, cells, cell_types, values, datadim=datadim)

    
def read_vtk(filename, tag = None, datadim=1):
    import vtk
    vtkmesh = read_dataset(filename)
    points = []
    cells = []
    pointdata = []
    cell_types = []
    points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
    print("Read " +filename)
    for i in range(vtkmesh.GetNumberOfCells()):
        cell = vtkmesh.GetCell(i)
        cell_type = cell.GetCellType()
        if cell_type not in [vtk.VTK_LINE, vtk.VTK_TRIANGLE]:
            continue
        cell_types.append(cell_type)
        entry = ()
        for j in range(cell.GetNumberOfPoints()):
            entry += (cell.GetPointId(j),)
        cells.append(entry)
    if not tag:
        # vtk Python utility method. Same as tag=="scalars"
        if datadim==1:
            fieldData = vtkmesh.GetPointData().GetScalars()
        if datadim >1:
            fieldData = vtkmesh.GetPointData().GetVectors()
    else:
        fieldData = vtkmesh.GetPointData().GetAbstractArray(tag)
    if fieldData:
        for i in range(vtkmesh.GetNumberOfPoints()):
            if datadim == 1:
                pointdata.append(fieldData.GetTuple1(i))
            elif datadim == 2:
                pointdata.append(fieldData.GetTuple2(i))
            elif datadim == 3:
                pointdata.append(fieldData.GetTuple3(i))
            else :
                raise Exception("Something weird is going on")
    return points, cells, cell_types, pointdata


def read_dataset(filename):
    import vtk
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
    elif (extension == ".pvtu"):
        reader = vtk.vtkXMLPUnstructuredGridReader() # Parallel XML format
    else:
        raise Exception("Unkown File extension: " + extension)
    reader.SetFileName(filename)
    reader.ReadAllScalarsOn()
    reader.ReadAllVectorsOn()
    reader.Update()
    return reader.GetOutput()


def read_conn(filename):
    try:
        import vtk
    except ImportError:
        VTK_LINE = 3
        VTK_TRIANGLE = 5
    else:
        VTK_LINE = vtk.VTK_LINE
        VTK_TRIANGLE = vtk.VTK_TRIANGLE
        
    with open(filename, "r") as fh:
        cells, cell_types = [], []
        for line in fh:
            coords = tuple([int(e) for e in line.split(" ")])
            assert(len(coords) in [2, 3])
            cells.append(coords)
            cell_types.append({2: VTK_LINE, 3: VTK_TRIANGLE}[len(coords)])
        assert(len(cells) == len(cell_types))
        return cells, cell_types


def read_txt(filename):
    points = []
    cells = []
    cell_types = []
    pointdata = []
    with open(filename, "r") as fh:
        for line in fh:
            point = ()
            parts = line.split(" ")
            parts_floats = [float(i) for i in parts]
            point = parts_floats[0:3]
            points.append(point)
            if len(parts_floats)==4:
                data = parts_floats[3]
            elif len(parts_floats)>4:
                data = parts_floats[3:]
                pointdata.append(data)
    base, ext = os.path.splitext(filename)
    connFileName = base + ".conn" + ext
    if os.path.exists(connFileName):
        cells, cell_types = read_conn(connFileName)

    return points, cells, cell_types, pointdata


def write_vtk(filename, points, cells = None, cell_types = None, pointdata = None, tag = None, datadim=1):
    import vtk
    data = vtk.vtkUnstructuredGrid() # is also vtkDataSet
    DataArray = vtk.vtkDoubleArray()
    DataArray.SetNumberOfComponents(datadim)
    pointdata = np.array(pointdata)
    if tag:
        DataArray.SetName(tag)
    vtkpoints = vtk.vtkPoints()
    for i, point in enumerate(points):
        vtkpoints.InsertPoint(i, point)
        if pointdata is not None and len(pointdata) > 0:
            if len(pointdata.shape) == 1 : # scalar case
                DataArray.InsertTuple1(i, pointdata[i])
            elif len(pointdata.shape) > 1 and pointdata.shape[1]==2: # two dimensional data
                DataArray.InsertTuple2(i, pointdata[i,0], pointdata[i,1])
            elif len(pointdata.shape) > 1 and pointdata.shape[1]==3: # 3D-data
                DataArray.InsertTuple3(i, pointdata[i,0], pointdata[i,1], pointdata[i,2])
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
    if len(pointdata.shape) == 1:
        print(pointdata.shape)
        pointData.SetScalars(DataArray)
        print("Writing scalar data...")
    else:
        pointData.SetVectors(DataArray)
        print("Writing Vector data...")
    write_dataset(filename, data)

    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(filename)
    writer.SetInputData(data)
    writer.Write()

    
def write_dataset(filename, dataset):
    import vtk
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

def write_txt(filename, points, cells = [], pointdata = None):
    with open(filename, "w") as fh:
        for i, point in enumerate(points):
            entry = (str(point[0]), str(point[1]), str(point[2]))
            if pointdata is not None and len(pointdata) > 0:
                if type(pointdata[0]) is float:
                    entry += (str(float(pointdata[i])),)
                elif len(pointdata[0])==3:
                    entry += (str(float(pointdata[i][0])), 
                              str(float(pointdata[i][1])), 
                              str(float(pointdata[i][2])))
                    
            fh.write(" ".join(entry) + "\n")

    base, ext = os.path.splitext(filename)
    connFileName = base + ".conn" + ext
    with open(connFileName, "w") as fh:
        fh.writelines([" ".join(map(str,cell))+"\n" for cell in cells])
