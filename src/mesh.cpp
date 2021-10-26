#include <boost/filesystem/operations.hpp>
#include <mesh.hpp>

#include <algorithm>
#include <boost/algorithm/string.hpp>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>

#include <vtkCell.h>
#include <vtkCellArray.h>
#include <vtkDoubleArray.h>
#include <vtkGenericDataObjectReader.h>
#include <vtkIdList.h>
#include <vtkLine.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkQuad.h>
#include <vtkSmartPointer.h>
#include <vtkTriangle.h>
#include <vtkUnstructuredGrid.h>
#include <vtkUnstructuredGridWriter.h>

namespace aste {

// --- MeshName

std::string MeshName::filename() const
{
  return _mname + ".vtk";
}

namespace aste {

}
namespace {
Mesh::VID vtkToPos(vtkIdType id)
{
  assert(id >= 0);
  return static_cast<Mesh::VID>(id);
}
} // namespace

namespace {
// Reads the main file containing the vertices and data
void readMainFile(Mesh &mesh, const std::string &filename, const std::string &dataname, const int &dim)
{
  if (!fs::is_regular_file(filename)) {
    throw std::invalid_argument{"The mesh file does not exist: " + filename};
  }

  vtkSmartPointer<vtkGenericDataObjectReader> reader =
      vtkSmartPointer<vtkGenericDataObjectReader>::New();
  reader->SetFileName(filename.c_str());
  reader->SetReadAllScalars(true);
  reader->SetReadAllVectors(true);
  reader->ReadAllFieldsOn();
  reader->Update();

  // Get Points
  vtkPoints *Points    = reader->GetUnstructuredGridOutput()->GetPoints();
  vtkIdType  NumPoints = reader->GetUnstructuredGridOutput()->GetNumberOfPoints();
  for (vtkIdType point = 0; point < NumPoints; point++) {
    std::array<double, 3> vertexPosArr;
    Points->GetPoint(point, vertexPosArr.data());
    mesh.positions.push_back(vertexPosArr);
  }
  // Get Point Data
  vtkPointData *PD = reader->GetUnstructuredGridOutput()->GetPointData();
  // Check it has data array
  if (PD->HasArray(dataname.c_str()) == 1) {
    // Get Data and Add to Mesh
    vtkDataArray *ArrayData = PD->GetArray(dataname.c_str());
    int           NumComp   = ArrayData->GetNumberOfComponents();

    if (NumComp != dim) {
      throw std::runtime_error("Dimensions of data provided and simulation does not match!.");
    }
    // Reserve enough space for data
    mesh.data.clear();
    mesh.data.reserve(NumPoints * dim);

    switch (NumComp) {
    case 1: // Scalar Data
      for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
        const double scalar = ArrayData->GetTuple1(tupleIdx);
        mesh.data.push_back(scalar);
      }
      break;
    case 2: // Vector Data with 2 component
      double *vector2ref;
      for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
        vector2ref = ArrayData->GetTuple2(tupleIdx);
        mesh.data.push_back(vector2ref[0]);
        mesh.data.push_back(vector2ref[1]);
      }
      break;
    case 3: // Vector Data with 3 component
      double *vector3ref;
      for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
        vector3ref = ArrayData->GetTuple3(tupleIdx);
        mesh.data.push_back(vector3ref[0]);
        mesh.data.push_back(vector3ref[1]);
        mesh.data.push_back(vector3ref[2]);
      }
      break;
    default: // Unknown number of component
      std::cerr << "Please check your VTK file there is/are " << NumComp << " component for data " << dataname << std::endl;
      throw std::runtime_error(std::string{"Dimensions of data provided = "}.append(std::to_string(NumComp)).append("and simulation = ").append(std::to_string(dim)).append("does not match for data =").append(dataname));
      break;
    }
  } else { // There is no data in mesh file fill with zeros.
    std::cout << "There is no data found for " << dataname << ". Dummy data will be used!.\n";
    mesh.data.resize(NumPoints * dim, 0.0);
  }

  for (int i = 0; i < reader->GetUnstructuredGridOutput()->GetNumberOfCells(); i++) {
    int cellType = reader->GetUnstructuredGridOutput()->GetCell(i)->GetCellType();

    //Here we use static cast since VTK library returns a long long unsigned int however preCICE uses int for PointId's
    if (cellType == VTK_TRIANGLE) {
      vtkCell *                cell = reader->GetUnstructuredGridOutput()->GetCell(i);
      std::array<Mesh::VID, 3> elem{vtkToPos(cell->GetPointId(0)), vtkToPos(cell->GetPointId(1)), vtkToPos(cell->GetPointId(2))};
      mesh.triangles.push_back(elem);
    } else if (cellType == VTK_LINE) {
      vtkCell *                cell = reader->GetUnstructuredGridOutput()->GetCell(i);
      std::array<Mesh::VID, 2> elem{vtkToPos(cell->GetPointId(0)), vtkToPos(cell->GetPointId(1))};
      mesh.edges.push_back(elem);
    } else if (cellType == VTK_QUAD) {
      vtkCell *                cell = reader->GetUnstructuredGridOutput()->GetCell(i);
      std::array<Mesh::VID, 4> elem{vtkToPos(cell->GetPointId(0)), vtkToPos(cell->GetPointId(1)), vtkToPos(cell->GetPointId(2)), vtkToPos(cell->GetPointId(3))};
      mesh.quadrilaterals.push_back(elem);
    } else {
      throw std::runtime_error{
          std::string{"Invalid cell type in VTK file. Valid cell types are, VTK_LINE, VTK_TRIANGLE, and VTK_QUAD."}};
    }
  }
}
} // namespace

Mesh MeshName::load(const int &dim, const std::string &dataname) const
{
  Mesh mesh;
  readMainFile(mesh, filename(), dataname, dim);
  return mesh;
}

void MeshName::createDirectories() const
{
  auto dir = fs::path(filename()).parent_path();
  if (!dir.empty()) {
    fs::create_directories(dir);
  }
}

void MeshName::save(const Mesh &mesh, const std::string &dataname) const
{
  const int                            numComp          = mesh.data.size() / mesh.positions.size();
  vtkSmartPointer<vtkUnstructuredGrid> unstructuredGrid = vtkSmartPointer<vtkUnstructuredGrid>::New();
  vtkSmartPointer<vtkPoints>           points           = vtkSmartPointer<vtkPoints>::New();
  vtkSmartPointer<vtkDoubleArray>      data             = vtkDoubleArray::New();

  data->SetName(dataname.c_str());
  data->SetNumberOfComponents(numComp);

  // Insert Points and Point Data
  for (size_t i = 0; i < mesh.positions.size(); i++) {
    points->InsertNextPoint(mesh.positions[i][0], mesh.positions[i][1], mesh.positions[i][2]);
    std::vector<double> pointData;
    for (int j = 0; j < numComp; j++) {
      pointData.push_back(mesh.data[i * numComp + j]);
    }
    data->InsertNextTuple(pointData.data());
  }

  unstructuredGrid->SetPoints(points);
  unstructuredGrid->GetPointData()->AddArray(data);

  // Connectivity Information
  vtkSmartPointer<vtkCellArray> cellArray = vtkSmartPointer<vtkCellArray>::New();

  std::vector<int> cellTypes;
  cellTypes.reserve(mesh.quadrilaterals.size() + mesh.triangles.size() + mesh.edges.size());

  if (mesh.quadrilaterals.size() > 0) {

    for (size_t i = 0; i < mesh.quadrilaterals.size(); i++) {
      vtkSmartPointer<vtkQuad> quadrilateral = vtkSmartPointer<vtkQuad>::New();
      quadrilateral->GetPointIds()->SetId(0, mesh.quadrilaterals[i][0]);
      quadrilateral->GetPointIds()->SetId(1, mesh.quadrilaterals[i][1]);
      quadrilateral->GetPointIds()->SetId(2, mesh.quadrilaterals[i][2]);
      quadrilateral->GetPointIds()->SetId(3, mesh.quadrilaterals[i][3]);

      cellArray->InsertNextCell(quadrilateral);
      cellTypes.push_back(VTK_QUAD);
    }
  }

  if (mesh.triangles.size() > 0) {
    for (size_t i = 0; i < mesh.triangles.size(); i++) {
      vtkSmartPointer<vtkTriangle> triangle = vtkSmartPointer<vtkTriangle>::New();
      triangle->GetPointIds()->SetId(0, mesh.triangles[i][0]);
      triangle->GetPointIds()->SetId(1, mesh.triangles[i][1]);
      triangle->GetPointIds()->SetId(2, mesh.triangles[i][2]);

      cellArray->InsertNextCell(triangle);
      cellTypes.push_back(VTK_TRIANGLE);
    }
  }

  if (mesh.edges.size() > 0) {
    for (size_t i = 0; i < mesh.edges.size(); i++) {
      vtkSmartPointer<vtkLine> line = vtkSmartPointer<vtkLine>::New();
      line->GetPointIds()->SetId(0, mesh.edges[i][0]);
      line->GetPointIds()->SetId(1, mesh.edges[i][1]);

      cellArray->InsertNextCell(line);
      cellTypes.push_back(VTK_LINE);
    }
  }

  unstructuredGrid->SetCells(cellTypes.data(), cellArray);

  // Write file
  vtkSmartPointer<vtkUnstructuredGridWriter> writer =
      vtkSmartPointer<vtkUnstructuredGridWriter>::New();
  writer->SetInputData(unstructuredGrid);
  writer->SetFileName(filename().c_str());

  writer->Write();
}

std::ostream &operator<<(std::ostream &out, const MeshName &mname)
{
  return out << mname.filename();
}

// --- BaseName

MeshName BaseName::with(const ExecutionContext &context) const
{
  if (context.isParallel()) {
    return {_bname + fs::path::preferred_separator + std::to_string(context.rank)};
  } else {
    return {_bname};
  }
}

std::vector<MeshName> BaseName::findAll(const ExecutionContext &context) const
{
  if (!context.isParallel()) {
    // Check single timestep/meshfiles first
    // Case: a single mesh
    if (fs::is_regular_file(_bname + ".vtk")) {
      return {MeshName{_bname}};
    }

    // Check multiple timesteps
    std::vector<MeshName> meshNames;
    for (int t = 1; true; ++t) {
      std::string stepMeshName = _bname + ".dt" + std::to_string(t);
      if (!fs::is_regular_file(stepMeshName + ".vtk"))
        break;
      meshNames.push_back(MeshName{stepMeshName});
    }
    {
      auto initMeshName = std::string{_bname + ".init" + ".vtk"};
      if (fs::is_regular_file(initMeshName))
        meshNames.push_back(MeshName{initMeshName});
    }
    {
      auto finalMeshName = std::string{_bname + ".final" + ".vtk"};
      if (fs::is_regular_file(finalMeshName))
        meshNames.push_back(MeshName{finalMeshName});
    }
    std::cerr << "Names: " << meshNames.size() << '\n';
    return meshNames;
  } else {
    fs::path rank{std::to_string(context.rank)};
    // Is there a single partitioned mesh?
    if (fs::is_directory(_bname)) {
      auto rankMeshName = (fs::path(_bname) / rank).string();
      if (fs::is_regular_file(rankMeshName + ".vtk")) {
        return {MeshName{rankMeshName}};
      }
    }

    // Check multiple timesteps
    std::vector<MeshName> meshNames;
    for (int t = 0; true; ++t) {
      fs::path stepDirectory{_bname + ".dt" + std::to_string(t)};
      auto     rankMeshName = (stepDirectory / rank).string();
      if (!(fs::is_directory(stepDirectory) && fs::is_regular_file(rankMeshName + ".vtk")))
        break;
      meshNames.push_back(MeshName{rankMeshName});
    }
    std::cerr << "Names: " << meshNames.size() << '\n';
    return meshNames;
  }
}

std::string Mesh::previewData(std::size_t max) const
{
  if (data.empty() || max == 0)
    return "<nothing>";

  std::stringstream oss;
  oss << data.front();
  for (size_t i = 1; i < std::min(max, data.size()); ++i)
    oss << ", " << data[i];
  oss << " ...";
  return oss.str();
}

std::string Mesh::summary() const
{
  std::stringstream oss;
  oss << positions.size() << " Vertices, " << data.size() << " Data Points, " << edges.size() << " Edges, " << triangles.size() << " Triangles" << quadrilaterals.size() << "Quadrilaterals";
  return oss.str();
}

/// Creates a unique and element-wise ordered set of undirected edges.
std::vector<Mesh::Edge> gather_unique_edges(const Mesh &mesh)
{
  std::vector<Mesh::Edge> sorted;
  sorted.reserve(mesh.edges.size() + 3 * mesh.triangles.size());

  for (auto const &edge : mesh.edges) {
    const auto a = edge[0];
    const auto b = edge[1];
    sorted.push_back(Mesh::Edge{std::min(a, b), std::max(a, b)});
  }

  for (auto const &triangle : mesh.triangles) {
    const auto a = triangle[0];
    const auto b = triangle[1];
    const auto c = triangle[2];
    sorted.push_back(Mesh::Edge{std::min(a, b), std::max(a, b)});
    sorted.push_back(Mesh::Edge{std::min(a, c), std::max(a, c)});
    sorted.push_back(Mesh::Edge{std::min(b, c), std::max(b, c)});
  }

  for (auto const &quadrilateral : mesh.quadrilaterals) {
    const auto a = quadrilateral[0];
    const auto b = quadrilateral[1];
    const auto c = quadrilateral[2];
    const auto d = quadrilateral[3];
    sorted.push_back(Mesh::Edge{std::min(a, b), std::max(a, b)});
    sorted.push_back(Mesh::Edge{std::min(a, d), std::max(a, d)});
    sorted.push_back(Mesh::Edge{std::min(b, c), std::max(b, c)});
    sorted.push_back(Mesh::Edge{std::min(c, d), std::max(c, d)});
  }

  std::sort(sorted.begin(), sorted.end(), EdgeCompare());
  auto end = std::unique(sorted.begin(), sorted.end());
  return std::vector<Mesh::Edge>(sorted.begin(), end);
}

} // namespace aste
