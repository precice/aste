"""
Mesh I/O utility script. One can read meshes from .vtk, .vtu, .vtp,... files
 and save to  .vtk and .vtu
"""

import os
import logging
import numpy as np
import itertools


class MeshIOError(Exception):
    pass


class MeshFormatError(MeshIOError):
    pass


class Mesh:
    def __init__(self, points=[], data=[], cells=[], edges=[], triangles=[],quads=[]):
        self._points = np.reshape(np.asarray(points, dtype=np.float64),
                                  (-1, 3))
        self._data = np.asarray(data, dtype=np.float64)

        if (cells):
            assert (not triangles)
            assert (not edges)
            self.cells = cells
        else:
            self._edges = np.reshape(np.asarray(edges, dtype=np.int32),
                                     (-1, 2))
            self._triangles = np.reshape(np.asarray(triangles, dtype=np.int32),
                                         (-1, 3))
            self._quads = np.reshape(np.asarray(quads, dtype=np.int32),
                                         (-1, 4))

    @classmethod
    def load(cls, meshname):
        points, cells, _, data = read_mesh(meshname)
        return cls(points, data, cells)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = np.float64(data)

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, points):
        self._points = np.reshape(np.asarray(points, np.float64), (-1, 3))

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, edges):
        if (edges):
            self._edges = np.unique(np.reshape(
                np.asarray(edges, dtype=np.int32), (-1, 2)),
                                    axis=0)
        else:
            self._edges = np.empty((0, 2))

    @property
    def triangles(self):
        return self._triangles

    @triangles.setter
    def triangles(self, triangles):
        if (triangles):
            self._triangles = np.unique(np.reshape(
                np.asarray(triangles, dtype=np.int32), (-1, 3)),
                                        axis=0)
        else:
            self._triangles = np.empty((0, 3))
            
    @property
    def quads(self):
        return self._quads

    @quads.setter
    def quads(self, quads):
        if (quads):
            self._triangles = np.unique(np.reshape(
                np.asarray(quads, dtype=np.int32), (-1, 4)),
                                        axis=0)
        else:
            self._quads = np.empty((0, 4))

    @property
    def cells(self):
        return self.edges.tolist() + self.triangles.tolist() + self.quads.tolist()

    @cells.setter
    def cells(self, cells):
        cellsbysize = {
            k: list(v)
            for k, v in itertools.groupby(cells, lambda cell: len(cell))
        }
        self.edges = list(cellsbysize.get(2, []))
        self.triangles = list(cellsbysize.get(3, []))
        self.quads = list(cellsbysize.get(4, []))
        self.validate()

    @property
    def empty(self):
        return self.points.size == 0

    @property
    def celltypes(self):
        edge_type = get_cell_type(2)
        triangle_type = get_cell_type(3)
        quad_type = get_cell_type(9)
        return np.append(np.full(len(self.edges), edge_type),
                         np.full(len(self.triangles), triangle_type))

    def __repr__(self):
        return "{} Vertices {} data, {} Cells".format(
            len(self.points), "with" if self.has_data() else "without",
            len(self.cells))

    def to_pandas(self):
        import pandas
        x, y, z = self.points.transpose()
        columns = {"x": x, "y": y, "z": z}
        if self.has_data():
            columns["data"] = self.data
        return pandas.DataFrame(columns)

    def save(self, filename):
        write_mesh(filename, self.points, self.cells, self.celltypes,
                   self.data)

    def save_to_vtk(self, filename):
        write_vtk(filename, self.points, self.cells, self.celltypes, self.data)

    def has_connectivity(self):
        return len(self.cells) > 0

    def has_data(self):
        return len(self.data) > 0

    def append(self, other):
        assert (isinstance(other, Mesh))
        if (not self.empty):
            assert (self.has_data() == other.has_data())
            assert (self.has_connectivity() == other.has_connectivity())

        offset = len(self.points)
        print(self)
        print(other)

        self._points = np.append(self.points, other.points, 0)
        self._data = np.append(self.data, other.data)
        self._edges = np.append(self.edges, other.edges + offset, 0)
        self._triangles = np.append(self.triangles, other.triangles + offset, 0)
        self._quads = np.append(self.quads, other.quads + offset, 0)
        print(self)

        self.validate()

    def validate(self):
        npoints = len(self._points)
        assert (len(self._data) in (0, npoints))
        assert (np.alltrue(self._edges < npoints))
        assert (np.alltrue(self._triangles < npoints))
        assert (np.alltrue(self._quads < npoints))
        if (self.edges.size > 0):
            assert (np.alltrue(
                np.unique(self._edges, axis=0, return_counts=True)[1] == 1))
        if (self.triangles.size > 0):
            assert (np.alltrue(
                np.unique(self._triangles, axis=0, return_counts=True)[1] == 1)
                    )
        if (self.quads.size > 0):
            assert (np.alltrue(
                np.unique(self._quads, axis=0, return_counts=True)[1] == 1)
                    )



def printable_cell_type(celltype):
    linetype = [3]
    triangletype = [5]
    quadtype = [9]

    try:
        import vtk
        linetype.append(vtk.VTK_LINE)
        triangletype.append(vtk.VTK_TRIANGLE)
        quadtype.append(vtk.VTK_QUAD)
    except ImportError:
        pass

    if celltype in linetype:
        return "line"
    elif celltype in triangletype:
        return "triangle"
    elif celltype in quadtype:
        return "quad"

    return None


def get_cell_type(cell):
    import collections
    if (isinstance(cell, collections.abc.Sequence)):
        elements = len(cell)
    else:
        elements = cell
    try:
        import vtk
    except ImportError:
        VTK_LINE = 3
        VTK_TRIANGLE = 5
        VTK_QUAD = 9
    else:
        VTK_LINE = vtk.VTK_LINE
        VTK_TRIANGLE = vtk.VTK_TRIANGLE
        VTK_QUAD = vtk.VTK_QUAD

    return {2: VTK_LINE, 3: VTK_TRIANGLE, 4: VTK_QUAD}.get(elements)


def read_mesh(filename, tag=None):
    """
    Returns Mesh Points, Mesh Cells, Mesh Celltypes, 
    Mesh Pointdata in this order
    """

    if not os.path.isfile(filename):
        logging.error(
            "Cannot read mesh with filename \"{}\".".format(filename))
        raise MeshFormatError()

    return read_vtk(filename, tag)


def write_mesh(filename, points, cells=None, cell_types=None, values=None):
    return write_vtk(filename, points, cells, cell_types, values)


def read_vtk(filename, tag=None):
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
        if cell_type not in [vtk.VTK_LINE, vtk.VTK_TRIANGLE,vtk.VTK_QUAD]:
            continue
        cell_types.append(cell_type)
        entry = ()
        for j in range(cell.GetNumberOfPoints()):
            entry += (cell.GetPointId(j), )
        cells.append(entry)
    if not tag:
        # vtk Python utility method. Same as tag=="scalars"
        fieldData = vtkmesh.GetPointData().GetScalars()
    else:
        fieldData = vtkmesh.GetPointData().GetAbstractArray(tag)
    if fieldData:
        for i in range(vtkmesh.GetNumberOfPoints()):
            pointdata.append(fieldData.GetTuple1(i))
    assert (len(pointdata) in [0, len(points)])
    assert (len(cell_types) in [0, len(cells)])
    return points, cells, cell_types, pointdata


def read_dataset(filename):
    import vtk
    extension = os.path.splitext(filename)[1]
    if (extension == ".vtk"):  # VTK Legacy format
        reader = vtk.vtkDataSetReader()
    elif (extension == ".vtp"):  # VTK XML Poly format
        reader = vtk.vtkXMLPolyDataReader()
    elif (extension == ".vtu"):  # VTK XML Unstructured format
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif (extension == ".stl"):  # Stereolithography format
        reader = vtk.vtkSTLReader()
    elif (extension == ".ply"):  # Stanford triangle format
        reader = vtk.vtkPLYReader()
    elif (extension == ".obj"):  # Wavefront OBJ format
        reader = vtk.vtkOBJReader()
    elif (extension == ".pvtu"):
        reader = vtk.vtkXMLPUnstructuredGridReader()  # Parallel XML format
    else:
        raise MeshFormatError()
    reader.SetFileName(filename)
    reader.Update()
    return reader.GetOutput()



def write_vtk(filename,
              points,
              cells=None,
              cell_types=None,
              pointdata=None,
              tag=None):
    if (cell_types is not None):
        assert (len(cell_types) in [0, len(cells)])
    if (pointdata is not None):
        assert (len(pointdata) in [0, len(points)])
    import vtk
    data = vtk.vtkUnstructuredGrid()  # is also vtkDataSet
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
    if (extension == ".vtk"):  # VTK Legacy format
        writer = vtk.vtkUnstructuredGridWriter()
    elif (extension == ".vtu"):  # VTK XML Unstructured Grid format
        writer = vtk.vtkXMLUnstructuredGridWriter()
    else:
        raise Exception("Unkown File extension: " + extension)
    writer.SetFileName(filename)
    writer.SetInputData(dataset)
    writer.Write()


