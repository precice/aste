""" 
Mesh I/O utility script. One can read meshes from .vtk, .txt, .vtu, .vtp,... files
 and save to .txt, .vtk and .vtu
"""

import os
import logging


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
        if cells is not None and len(cells) > 0:
            logging.warning("Saving as .txt discards topology")
        return write_txt(filename, points, values) # TODO: Warn on cells
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
    for i in range(vtkmesh.GetNumberOfCells()):
        cell = vtkmesh.GetCell(i)
        cell_types.append(cell.GetCellType())
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


def write_vtk(filename, points, cells = None, cell_types = None, pointdata = None, tag = None, datadim=1):
    import vtk
    data = vtk.vtkUnstructuredGrid() # is also vtkDataSet
    DataArray = vtk.vtkDoubleArray()
    DataArray.SetNumberOfComponents(datadim)
    if tag:
        DataArray.SetName(tag)
    vtkpoints = vtk.vtkPoints()
    for i, point in enumerate(points):
        vtkpoints.InsertPoint(i, point)
        if pointdata is not None and len(pointdata) > 0:
            if len(pointdata.shape) == 1 or pointdata.shape[1]==1: #scalar data
                DataArray.InsertTuple1(i, pointdata[i])
            elif len(pointdata.shape) > 1 and pointdata.shape[1]==2: #two dimensional data
                DataArray.InsertTuple2(i, pointdata[i,0], pointdata[i,1])
            elif len(pointdata.shape) > 1 and pointdata.shape[1]==3: #3D-data
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
    if len(pointdata.shape) == 1 or pointdata.shape[1]==1:
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

def write_txt(filename, points, pointdata = None):
    with open(filename, "w") as fh:
        for i, point in enumerate(points):
            entry = (str(point[0]), str(point[1]), str(point[2]))
            if pointdata is not None and len(pointdata) > 0:
                if len(pointdata[0]) ==1:
                    entry += (str(float(pointdata[i])),)
                elif len(pointdata[0])==2:
                    entry += (str(float(pointdata[i,0])), str(float(pointdata[i,1])))
                elif len(pointdata[0])==3:
                    #print(pointdata[i])
                    entry += (str(float(pointdata[i][0])), 
                              str(float(pointdata[i][1])), 
                              str(float(pointdata[i][2])))

            fh.write(" ".join(entry) + "\n")
