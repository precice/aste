#include <algorithm>
#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/filesystem/operations.hpp>
#include <fstream>
#include <iostream>
#include <limits>
#include <mesh.hpp>
#include <mpi.h>
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
  return _mname + _ext;
}

Mesh::VID vtkToPos(vtkIdType id)
{
  assert(id >= 0);
  return static_cast<Mesh::VID>(id);
}

// Read vertices and mesh connectivity
void readMesh(Mesh &mesh, const std::string &filename, const int dim)
{
  if (!fs::is_regular_file(filename)) {
    std::cerr << "The mesh file does not exist: " << filename;
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
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
    std::cerr << "Unknown File Extension for file " << filename << "Extension should be .vtk or .vtu";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  // Get Points
  vtkPoints *Points    = grid->GetPoints();
  vtkIdType  NumPoints = grid->GetNumberOfPoints();
  for (vtkIdType point = 0; point < NumPoints; point++) {
    std::array<double, 3> vertexPosArr;
    Points->GetPoint(point, vertexPosArr.data());
    std::vector<double> vertexLoc(dim);
    std::copy(vertexPosArr.begin(), vertexPosArr.begin() + dim, vertexLoc.begin());
    mesh.positions.push_back(vertexLoc);
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
      std::cerr << "Invalid cell type in VTK file. Valid cell types are, VTK_LINE, VTK_TRIANGLE, and VTK_QUAD.";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
  }
};

// Read required data from mesh file
void readData(Mesh &mesh, const std::string &filename)
{
  if (!fs::is_regular_file(filename)) {
    std::cerr << "The mesh file does not exist: " << filename;
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  mesh.fname                               = filename; // Store data loaded from which mesh
  auto                                 ext = fs::path(filename).extension();
  vtkSmartPointer<vtkUnstructuredGrid> grid;

  if (ext == ".vtk") {
    vtkSmartPointer<vtkUnstructuredGridReader> reader = vtkSmartPointer<vtkUnstructuredGridReader>::New();
    reader->SetFileName(filename.c_str());
    reader->ReadAllScalarsOn();
    reader->ReadAllVectorsOn();
    reader->ReadAllFieldsOn();
    reader->Update();
    grid = reader->GetOutput();
  } else if (ext == ".vtu") {
    vtkSmartPointer<vtkXMLUnstructuredGridReader> reader = vtkSmartPointer<vtkXMLUnstructuredGridReader>::New();
    reader->SetFileName(filename.c_str());
    reader->Update();
    grid = reader->GetOutput();
  } else {
    std::cerr << "Unknown File Extension for file " << filename << "Extension should be .vtk or .vtu";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  vtkIdType NumPoints = grid->GetNumberOfPoints();
  // Get Point Data
  vtkPointData *PD = grid->GetPointData();
  // Check it has data array
  for (auto &data : mesh.meshdata) {
    auto dataname = data.name;
    auto datatype = data.type;
    if ((PD->HasArray(dataname.c_str()) == 1) && (datatype == aste::datatype::WRITE)) {
      // Get Data and Add to Mesh
      vtkDataArray *ArrayData = PD->GetArray(dataname.c_str());
      int           NumComp   = ArrayData->GetNumberOfComponents();

      assert(NumComp >= data.numcomp); // 3D case it should match 2D case it match or less
      data.dataVector.reserve(NumComp * NumPoints);

      switch (NumComp) {
      case 1: // Scalar Data
        assert(data.numcomp == 1);
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          const double scalar = ArrayData->GetTuple1(tupleIdx);
          data.dataVector.push_back(scalar);
        }
        break;
      case 2: // Vector Data with 2 component
        assert(data.numcomp == 2);
        double *vector2ref;
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          vector2ref = ArrayData->GetTuple2(tupleIdx);
          std::copy_n(vector2ref, 2, std::back_inserter(data.dataVector));
        }
        break;
      case 3: // Vector Data with 3 component
        double *vector3ref;
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          vector3ref = ArrayData->GetTuple3(tupleIdx);
          std::copy_n(vector3ref, data.numcomp, std::back_inserter(data.dataVector));
        }
        break;
      default: // Unknown number of component
        std::cerr << std::string("Please check your VTK file there is/are ").append(std::string(std::to_string(NumComp))).append(" component for data ").append(dataname);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        break;
      }
    } else if (datatype == aste::datatype::GRADIENT) {
      const int gradDim = data.gradDimension; // Number of components of gradient
      // Get Data and Add to Mesh
      vtkDataArray *gradX, *gradY, *gradZ;

      (PD->HasArray("gradientx")) ? gradX = PD->GetArray("gradientx") : gradX = nullptr;
      (PD->HasArray("gradienty")) ? gradY = PD->GetArray("gradienty") : gradY = nullptr;
      (PD->HasArray("gradientz")) ? gradZ = PD->GetArray("gradientz") : gradZ = nullptr;

      if (gradX == nullptr || gradY == nullptr || (gradDim == 3 && gradZ == nullptr)) {
        std::cerr << "Error while parsing gradient data, please check your input mesh";
      }

      int NumComp = gradX->GetNumberOfComponents();

      assert(NumComp >= data.numcomp); // 3D case it should match 2D case it match or less
      data.dataVector.reserve(NumComp * gradDim * NumPoints);

      switch (NumComp) {
      case 1: // Scalar Data
        assert(data.numcomp == 1);
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          const double x = gradX->GetTuple1(tupleIdx);
          const double y = gradY->GetTuple1(tupleIdx);
          data.dataVector.push_back(x);
          data.dataVector.push_back(y);
          if (gradDim == 3) {
            const double z = gradZ->GetTuple1(tupleIdx);
            data.dataVector.push_back(z);
          }
        }
        break;
      case 2: // Vector Data with 2 component
      {
        assert(data.numcomp == 2);
        double *x, *y;
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          x = gradX->GetTuple2(tupleIdx);
          y = gradY->GetTuple2(tupleIdx);
          std::copy_n(x, 2, std::back_inserter(data.dataVector));
          std::copy_n(y, 2, std::back_inserter(data.dataVector));
        }
        break;
      }
      case 3: // Vector Data with 3 component
      {
        double    *x, *y, *z;
        const bool haveGradZ = (gradZ != nullptr);
        for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++) {
          x = gradX->GetTuple3(tupleIdx);
          std::copy_n(x, data.numcomp, std::back_inserter(data.dataVector));
          y = gradY->GetTuple3(tupleIdx);
          std::copy_n(y, data.numcomp, std::back_inserter(data.dataVector));
          if (haveGradZ) {
            z = gradZ->GetTuple3(tupleIdx);
            std::copy_n(z, data.numcomp, std::back_inserter(data.dataVector));
          }
        }
        break;
      }
      default: // Unknown number of component
        std::cerr << std::string("Please check your VTK file there is/are ").append(std::string(std::to_string(NumComp))).append(" component for data ").append(dataname);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        break;
      }
    }
  }
};

void MeshName::loadMesh(Mesh &mesh, const int dim)
{
  readMesh(mesh, filename(), dim);
}

void MeshName::loadData(Mesh &mesh)
{
  readData(mesh, filename());
}

void MeshName::resetData(Mesh &mesh)
{
  for (auto &data : mesh.meshdata) {
    data.dataVector.clear();
  }
}

void MeshName::createDirectories() const
{
  auto dir = fs::path(filename()).parent_path();
  if (!dir.empty()) {
    fs::create_directories(dir);
  }
}

void MeshName::save(const Mesh &mesh, const std::string &outputFileName) const
{

  auto                                 ext = fs::path(mesh.fname).extension();
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
    std::cerr << "Unknown File Extension for file " << mesh.fname << " Extension should be .vtk or .vtu";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  for (const auto meshdata : mesh.meshdata) {
    vtkSmartPointer<vtkDoubleArray>
        vtkdata = vtkDoubleArray::New();
    vtkdata->SetName(meshdata.name.c_str());
    vtkdata->SetNumberOfComponents(meshdata.numcomp);

    std::vector<double> pointData;
    pointData.reserve(3);
    for (size_t i = 0; i < grid->GetNumberOfPoints(); i++) {
      for (int j = 0; j < meshdata.numcomp; j++) {
        pointData.push_back(meshdata.dataVector[i * meshdata.numcomp + j]);
      }
      vtkdata->InsertNextTuple(pointData.data());
      pointData.clear();
    }

    grid->GetPointData()->AddArray(vtkdata);
  }

  // Write file
  if (_context.isParallel()) {
    vtkSmartPointer<vtkXMLUnstructuredGridWriter> writer =
        vtkSmartPointer<vtkXMLUnstructuredGridWriter>::New();
    writer->SetInputData(grid);
    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    auto outputFileName_withCont = outputFileName + "_" + std::to_string(rank) + ext.string();
    writer->SetFileName(outputFileName_withCont.c_str());
    writer->Write();

  } else {
    vtkSmartPointer<vtkUnstructuredGridWriter> writer =
        vtkSmartPointer<vtkUnstructuredGridWriter>::New();
    writer->SetInputData(grid);
    auto outputFileName_withCont = outputFileName + ext.string();
    writer->SetFileName(outputFileName_withCont.c_str());
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
    return {_bname + "_" + std::to_string(context.rank), ".vtu", context};
  } else {
    return {_bname, ".vtk", context};
  }
}

std::vector<MeshName> BaseName::findAll(const ExecutionContext &context) const
{
  if (!context.isParallel()) {
    // Check single timestep/meshfiles first
    std::vector<std::string> extensions{".vtk", ".vtu"};
    // Case: a single mesh
    for (const auto ext : extensions) {
      if (fs::is_regular_file(_bname + ext)) {
        return {MeshName{_bname, ext, context}};
      }

      // Check multiple timesteps
      std::vector<MeshName> meshNames;
      {
        auto initMeshName = std::string{_bname + ".init"};
        if (fs::is_regular_file(initMeshName + ext))
          meshNames.emplace_back(MeshName{initMeshName, ext, context});
      }
      for (int t = 1; true; ++t) {
        std::string stepMeshName = _bname + ".dt" + std::to_string(t);
        if (!fs::is_regular_file(stepMeshName + ext))
          break;
        meshNames.emplace_back(MeshName{stepMeshName, ext, context});
      }
      if (!meshNames.empty()) {
        std::cerr << "Total number of detected meshes: " << meshNames.size() << '\n';
        return meshNames;
      }
    }

  } else { // Parallel Case
    // Check if there is a single mesh
    std::string ext{".vtu"};
    std::string rankMeshName{_bname + "_" + std::to_string(context.rank)};
    if (fs::is_regular_file(rankMeshName + ext)) {
      return {MeshName{rankMeshName, ext, context}};
    }
    // Check multiple timesteps
    std::vector<MeshName> meshNames;
    {
      auto initMeshName = std::string{_bname + ".init" + "_" + std::to_string(context.rank)};
      if (fs::is_regular_file(initMeshName + ext))
        meshNames.emplace_back(MeshName{initMeshName, ext, context});
    }
    for (int t = 1; true; ++t) {
      std::string rankMeshName{_bname + ".dt" + std::to_string(t) + "_" + std::to_string(context.rank)};
      if (!fs::is_regular_file(rankMeshName + ext))
        break;
      meshNames.emplace_back(rankMeshName, ext, context);
    }
    std::cerr << "Total number of detected meshes: " << meshNames.size() << '\n';
    return meshNames;
  }
  std::cerr << "Unable to handle basename " << _bname << " no meshes found";
  MPI_Finalize();
  std::exit(EXIT_FAILURE);
}

std::string Mesh::previewData(std::size_t max) const
{

  if (meshdata.empty() || max == 0)
    return "<nothing>";

  std::stringstream oss;
  for (const auto data : meshdata) {
    oss << data.name;
    oss << data.dataVector.front();
    for (size_t i = 1; i < std::min(max, data.dataVector.size()); ++i)
      oss << ", " << data.dataVector[i];
    oss << " ...";
  }
  return oss.str();
}

std::string Mesh::previewData(const MeshData &data, std::size_t max) const
{

  if (data.dataVector.empty() || max == 0)
    return "<nothing>";

  std::stringstream oss;
  oss << data.name << "  ";
  oss << data.dataVector.front();
  for (size_t i = 1; i < std::min(max, data.dataVector.size()); ++i)
    oss << ", " << data.dataVector[i];
  oss << " ...";

  return oss.str();
}

std::string Mesh::summary() const
{

  std::stringstream oss;
  oss << positions.size() << " Vertices, " << meshdata.size() << " Data arrays, " << edges.size() << " Edges, " << triangles.size() << " Triangles " << quadrilaterals.size() << " Quadrilaterals ";
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
