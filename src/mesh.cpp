#include <boost/filesystem.hpp>
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
#include <vtkIdList.h>
#include <vtkLine.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkQuad.h>
#include <vtkSmartPointer.h>
#include <vtkTriangle.h>
#include <vtkUnstructuredGrid.h>
#include <vtkUnstructuredGridReader.h>
#include <vtkUnstructuredGridWriter.h>
#include <vtkXMLUnstructuredGridReader.h>
#include <vtkXMLUnstructuredGridWriter.h>

namespace aste {

// --- MeshName

std::string MeshName::filename() const
{
  if (_context.isParallel()) {
    return _mname + ".vtu";
  } else {
    return _mname + ".vtk";
  }
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

  mesh.fname                               = filename; // Store data loaded from which mesh
  auto                                 ext = fs::path(filename).extension();
  vtkSmartPointer<vtkUnstructuredGrid> grid;

  if (ext == ".vtk") {
    vtkSmartPointer<vtkUnstructuredGridReader> reader = vtkSmartPointer<vtkUnstructuredGridReader>::New();
    reader->SetFileName(filename.c_str());
    reader->Update();
    grid = reader->GetOutput();
  } else if (ext == ".vtu") {
    vtkSmartPointer<vtkXMLUnstructuredGridReader> reader = vtkSmartPointer<vtkXMLUnstructuredGridReader>::New();
    reader->SetFileName(filename.c_str());
    reader->Update();
    grid = reader->GetOutput();
  } else {
    throw std::runtime_error("Unknown File Extension for file " + filename + "Extension should be .vtk or .vtu");
  }

  // Get Points
  vtkPoints *Points    = grid->GetPoints();
  vtkIdType  NumPoints = grid->GetNumberOfPoints();
  for (vtkIdType point = 0; point < NumPoints; point++) {
    std::array<double, 3> vertexPosArr;
    Points->GetPoint(point, vertexPosArr.data());
    mesh.positions.push_back(vertexPosArr);
  }
  // Get Point Data
  vtkPointData *PD = grid->GetPointData();
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

  for (int i = 0; i < grid->GetNumberOfCells(); i++) {
    int cellType = grid->GetCell(i)->GetCellType();

    // Here we use static cast since VTK library returns a long long unsigned int however preCICE uses int for PointId's
    if (cellType == VTK_TRIANGLE) {
      vtkCell                 *cell = grid->GetCell(i);
      std::array<Mesh::VID, 3> elem{vtkToPos(cell->GetPointId(0)), vtkToPos(cell->GetPointId(1)), vtkToPos(cell->GetPointId(2))};
      mesh.triangles.push_back(elem);
    } else if (cellType == VTK_LINE) {
      vtkCell                 *cell = grid->GetCell(i);
      std::array<Mesh::VID, 2> elem{vtkToPos(cell->GetPointId(0)), vtkToPos(cell->GetPointId(1))};
      mesh.edges.push_back(elem);
    } else if (cellType == VTK_QUAD) {
      vtkCell                 *cell = grid->GetCell(i);
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
  const int                            numComp = mesh.data.size() / mesh.positions.size();
  vtkSmartPointer<vtkDoubleArray>      data    = vtkDoubleArray::New();
  auto                                 ext     = fs::path(mesh.fname).extension();
  vtkSmartPointer<vtkUnstructuredGrid> grid;
  if (ext == ".vtk") {
    vtkSmartPointer<vtkUnstructuredGridReader> reader = vtkSmartPointer<vtkUnstructuredGridReader>::New();
    reader->SetFileName(mesh.fname.c_str());
    reader->Update();
    grid = reader->GetOutput();
  } else if (ext == ".vtu") {
    vtkSmartPointer<vtkXMLUnstructuredGridReader> reader = vtkSmartPointer<vtkXMLUnstructuredGridReader>::New();
    reader->SetFileName(mesh.fname.c_str());
    reader->Update();
    grid = reader->GetOutput();
  } else {
    throw std::runtime_error("Unknown File Extension for file " + mesh.fname + "Extension should be .vtk or .vtu");
  }

  data->SetName(dataname.c_str());
  data->SetNumberOfComponents(numComp);

  // Insert Point Data
  {
    std::vector<double> pointData;
    pointData.reserve(3);
    for (size_t i = 0; i < mesh.positions.size(); i++) {
      for (int j = 0; j < numComp; j++) {
        pointData.push_back(mesh.data[i * numComp + j]);
      }
      data->InsertNextTuple(pointData.data());
      pointData.clear();
    }
  }

  grid->GetPointData()->AddArray(data);

  // Write file
  if (_context.isParallel()) {
    vtkSmartPointer<vtkXMLUnstructuredGridWriter> writer =
        vtkSmartPointer<vtkXMLUnstructuredGridWriter>::New();
    writer->SetInputData(grid);
    writer->SetFileName(filename().c_str());
    writer->Write();

  } else {
    vtkSmartPointer<vtkUnstructuredGridWriter> writer =
        vtkSmartPointer<vtkUnstructuredGridWriter>::New();
    writer->SetInputData(grid);
    writer->SetFileName(filename().c_str());
    writer->SetFileTypeToBinary();
    writer->Write();
  }
}

std::ostream &operator<<(std::ostream &out, const MeshName &mname)
{
  return out << mname.filename();
}

// --- BaseName

MeshName BaseName::with(const ExecutionContext &context) const
{
  if (context.isParallel()) {
    return {_bname + "_" + std::to_string(context.rank), context};
  } else {
    return {_bname, context};
  }
}

std::vector<MeshName> BaseName::findAll(const ExecutionContext &context) const
{
  if (!context.isParallel()) {
    // Check single timestep/meshfiles first
    // Case: a single mesh
    if (fs::is_regular_file(_bname + ".vtk")) {
      return {MeshName{_bname, context}};
    }

    // Check multiple timesteps
    std::vector<MeshName> meshNames;
    {
      auto initMeshName = std::string{_bname + ".init"};
      if (fs::is_regular_file(initMeshName + ".vtk"))
        meshNames.push_back(MeshName{initMeshName, context});
    }
    for (int t = 1; true; ++t) {
      std::string stepMeshName = _bname + ".dt" + std::to_string(t);
      if (!fs::is_regular_file(stepMeshName + ".vtk"))
        break;
      meshNames.push_back(MeshName{stepMeshName, context});
    }
    {
      auto finalMeshName = std::string{_bname + ".final"};
      if (fs::is_regular_file(finalMeshName + ".vtk"))
        meshNames.push_back(MeshName{finalMeshName, context});
    }
    std::cerr << "Names: " << meshNames.size() << '\n';
    return meshNames;

  } else { // Parallel Case
    // Check if there is a single mesh
    std::string rankMeshName{_bname + "_" + std::to_string(context.rank)};
    if (fs::is_regular_file(rankMeshName + ".vtu")) {
      return {MeshName{rankMeshName, context}};
    }

    // Check multiple timesteps
    std::vector<MeshName> meshNames;
    {
      auto initMeshName = std::string{_bname + ".init" + "_" + std::to_string(context.rank)};
      if (fs::is_regular_file(initMeshName + ".vtu"))
        meshNames.push_back(MeshName{initMeshName, context});
    }
    for (int t = 1; true; ++t) {
      std::string rankMeshName{_bname + ".dt" + std::to_string(t) + "_" + std::to_string(context.rank)};
      if (!fs::is_regular_file(rankMeshName + ".vtu"))
        break;
      meshNames.push_back(MeshName{rankMeshName, context});
    }
    {
      auto finalMeshName = std::string{_bname + ".final" + "_" + std::to_string(context.rank)};
      if (fs::is_regular_file(finalMeshName + ".vtu"))
        meshNames.push_back(MeshName{finalMeshName, context});
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
  oss << positions.size() << " Vertices, " << data.size() << " Data Points, " << edges.size() << " Edges, " << triangles.size() << " Triangles " << quadrilaterals.size() << " Quadrilaterals ";
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
