""" 
Mesh I/O utility script. One can read meshes from .vtk, .txt, .vtu, .vtp,... files
 and save to .txt, .vtk and .vtu
"""

import os
import logging


class MeshIOError(Exception):
    pass


class MeshFormatError(MeshIOError):
    pass


def get_cell_type(cell):
    try:
        import vtk
    except ImportError:
        VTK_LINE = 3
        VTK_TRIANGLE = 5
    else:
        VTK_LINE = vtk.VTK_LINE
        VTK_TRIANGLE = vtk.VTK_TRIANGLE

    return {2: VTK_LINE, 3: VTK_TRIANGLE}[len(cell)]


def read_mesh(filename, tag = None):
    """
    Returns Mesh Points, Mesh Cells, Mesh Celltypes, 
    Mesh Pointdata in this order
    """
    if os.path.isdir(filename):
        logging.error("Reading of partitioned meshes is not supported. Join it first using join_mesh.")
        raise MeshFormatError()
        
    if not os.path.isfile(filename):
        logging.error("Cannot read mesh with filename \"{}\".".format(filename))
        raise MeshFormatError()

    if os.path.splitext(filename)[1] == ".txt":
        return read_txt(filename)
    else:
        return read_vtk(filename, tag)

    
def write_mesh(filename, points, cells = None, cell_types = None, values = None):
    if os.path.splitext(filename)[1] == ".txt":
        return write_txt(filename, points, cells, values)
    else:
        return write_vtk(filename, points, cells, cell_types, values)

    
def read_vtk(filename, tag = None):
    import vtk
    vtkmesh = read_dataset(filename)
    points = []
    cells = []
    pointdata = []
    cell_types = []
    points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
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
        fieldData = vtkmesh.GetPointData().GetScalars()
    else:
        fieldData = vtkmesh.GetPointData().GetAbstractArray(tag)
    if fieldData:
        for i in range(vtkmesh.GetNumberOfPoints()):
            pointdata.append(fieldData.GetTuple1(i))
    assert(len(pointdata) in [0, len(points)])
    assert(len(cell_types) in [0, len(cells)])
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
        raise MeshFormatError()
    reader.SetFileName(filename)
    reader.Update()
    return reader.GetOutput()


def read_conn(filename):
    with open(filename, "r") as fh:
        cells, cell_types = [], []
        for line in fh:
            coords = tuple([int(e) for e in line.split(" ")])
            assert(len(coords) in [2, 3])
            cells.append(coords)
            cell_types.append(get_cell_type(coords))
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
            for i in range(3):
                point += (float(parts[i]),)
            points.append(point)
            if len(parts) > 3:
                pointdata.append(float(parts[3]))
    base, ext = os.path.splitext(filename)
    connFileName = base + ".conn" + ext
    if os.path.exists(connFileName):
        cells, cell_types = read_conn(connFileName)

    assert(len(pointdata) in [0, len(points)])
    assert(len(cell_types) in [0, len(cells)])
    return points, cells, cell_types, pointdata


def write_vtk(filename, points, cells = None, cell_types = None, pointdata = None, tag = None):
    if(cell_types is not None):
        assert(len(cell_types) in [0, len(cells)])
    if(pointdata is not None):
        assert(len(pointdata) in [0, len(points)])
    import vtk
    data = vtk.vtkUnstructuredGrid() # is also vtkDataSet
    scalars = vtk.vtkDoubleArray()
    if tag:
        scalars.SetName(tag)
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
    assert(len(pointdata) in [0, len(points)])

    base, ext = os.path.splitext(filename)
    if (ext != ".txt"):
        base = filename
        ext = ".txt"
    mainFileName = base + ext

    with open(mainFileName, "w") as fh:
        for i, point in enumerate(points):
            entry = (str(point[0]), str(point[1]), str(point[2]))
            if pointdata is not None and len(pointdata) > 0:
                entry += (str(float(pointdata[i])),)
            fh.write(" ".join(entry) + "\n")

    connFileName = base + ".conn" + ext
    with open(connFileName, "w") as fh:
        fh.writelines([" ".join(map(str,cell))+"\n" for cell in cells])
