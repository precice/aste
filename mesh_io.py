def read_mesh(filename):
    if filename[-4:] == ".vtk":
        return read_vtk(filename)
    else:
        return read_txt(filename)
def write_mesh(filename, points, cells = None, values = None):
    if filename[-4:] == ".vtk":
        return write_vtk(filename, points, cells, values)
    else:
        # TODO: Warn on cells
        return write_txt(filename, points, values)

def read_vtk(filename):
    import vtk
    result = []
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(filename)
    reader.Update()
    vtkmesh = reader.GetOutput()
    points = []
    cells = []
    pointdata = []
    points = [vtkmesh.GetPoint(i) for i in range(vtkmesh.GetNumberOfPoints())]
    for i in range(vtkmesh.GetNumberOfCells()):
        cell = vtkmesh.GetCell(i)
        entry = ()
        for j in range(cell.GetNumberOfPoints()):
            entry += (cell.GetPointId(j),)
        cells.append(entry)
    fieldData = vtkmesh.GetPointData().GetScalars()
    if fieldData:
        for i in range(vtkmesh.GetNumberOfPoints()):
            pointdata.append(fieldData.GetTuple1(i))
    return points, cells, pointdata
def read_txt(filename):
    points = []
    cells = []
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
    return points, cells, pointdata

def write_vtk(filename, points, cells = None, pointdata = None):
    import vtk
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(filename)
    data = vtk.vtkUnstructuredGrid() # is also vtkDataSet
    scalars = vtk.vtkDoubleArray()
    vtkpoints = vtk.vtkPoints()
    for i, point in enumerate(points):
        vtkpoints.InsertPoint(i, point)
        if pointdata is not None and len(pointdata) > 0:
            scalars.InsertTuple1(i, pointdata[i])
    if cells:
        pass # TODO: Add cells to vtk mesh
    pointData = data.GetPointData()
    pointData.SetScalars(scalars)
    data.SetPoints(vtkpoints)
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetFileName(filename)
    writer.SetInputData(data)
    writer.Write()
def write_txt(filename, points, pointdata = None):
    with open(filename, "w") as fh:
        for i, point in enumerate(points):
            entry = (str(point[0]), str(point[1]), str(point[2]))
            if pointdata is not None and len(pointdata) > 0:
                entry += (str(float(pointdata[i])),)
            fh.write(" ".join(entry) + "\n")
