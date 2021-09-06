#include <boost/filesystem/operations.hpp>
#include <mesh.hpp>

#include <iostream>
#include <fstream>
#include <sstream>
#include <limits>
#include <algorithm>
#include <boost/algorithm/string.hpp>

#include <vtkGenericDataObjectReader.h>
#include <vtkSmartPointer.h>
#include <vtkPoints.h>
#include <vtkUnstructuredGrid.h>
#include <vtkPointData.h>
#include <vtkDoubleArray.h>
#include <vtkUnstructuredGridWriter.h>


namespace aste
{

  // --- MeshName

  std::string MeshName::filename() const { return _mname + ".vtk"; }

  void MeshName::setDataname(std::string dataname) { _dname = dataname; }

  std::string MeshName::dataname() const { return _dname; }

  std::string MeshName::connectivityfilename() const { return _mname + ".conn.txt"; }

  namespace
  {
    // Reads the main file containing the vertices and data
    void readMainFile(Mesh &mesh, const std::string &filename, const std::string &dataname)
    {

      if (!fs::is_regular_file(filename))
      {
        throw std::invalid_argument{"The mesh file does not exist: " + filename};
      }

      vtkSmartPointer<vtkGenericDataObjectReader> reader =
          vtkSmartPointer<vtkGenericDataObjectReader>::New();
      reader->SetFileName(filename.c_str());
      reader->SetReadAllScalars(true);
      reader->SetReadAllVectors(true);
      reader->ReadAllFieldsOn();
      reader->Update();

      //Get Points
      vtkPoints *Points = reader->GetUnstructuredGridOutput()->GetPoints();
      vtkIdType NumPoints = reader->GetUnstructuredGridOutput()->GetNumberOfPoints();
      double vertexPos[3];
      for (vtkIdType point = 0; point < NumPoints; point++)
      {
        Points->GetPoint(point, vertexPos);
        // std::cout << "vertex = " << point <<  "x = " <<  vertexPos[0] << " y = " << vertexPos[1] << " z = " << vertexPos[2] << std::endl;
        std::array<double, 3> vertexPosArr{vertexPos[0], vertexPos[1], vertexPos[2]};
        mesh.positions.push_back(vertexPosArr);
      }

      // Get Point Data
      vtkPointData *PD = reader->GetUnstructuredGridOutput()->GetPointData();
      // Check it has data array

      int check = PD->HasArray(dataname.c_str());
      if (check == 1)
      {
        // Get Data and Add to Mesh
        vtkDataArray *ArrayData = PD->GetArray(dataname.c_str());
        int NumComp = ArrayData->GetNumberOfComponents();
        switch (NumComp)
        {
        case 1: // Scalar
          double scalar;
          for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++)
          {
            scalar = ArrayData->GetTuple1(tupleIdx);
            mesh.data.push_back(scalar);
          }
          break;

        case 3: // Vector ?????
          double *vectorref;
          for (vtkIdType tupleIdx = 0; tupleIdx < NumPoints; tupleIdx++)
          {
            vectorref = ArrayData->GetTuple3(tupleIdx);
          }
          break;
        }
      }
      else
      { // Threre is no data in mesh file fill with zeros.  
        mesh.data.resize(NumPoints);
        std::fill(mesh.data.begin(), mesh.data.end(), 0.0);
       /*
        for (vtkIdType point = 0; point < NumPoints; point++)
        {
          mesh.data.push_back(0.0);
        }
        */
      }
    }

    // Reads the connectivity file containing the triangle and edge information
    void readConnFile(Mesh &mesh, const std::string &filename)
    {
      if (!fs::is_regular_file(filename))
      {
        throw std::invalid_argument{"The mesh connectivity file does not exist: " + filename};
      }
      std::ifstream connFile{filename};
      std::string line;
      while (std::getline(connFile, line))
      {
        std::vector<std::string> parts;
        boost::split(parts, line, [](char c)
                     { return c == ' '; });
        std::vector<size_t> indices(parts.size());
        std::transform(parts.begin(), parts.end(), indices.begin(), [](const std::string &s) -> size_t
                       { return std::stol(s); });

        if (indices.size() == 3)
        {
          std::array<size_t, 3> elem{indices[0], indices[1], indices[2]};
          mesh.triangles.push_back(elem);
        }
        else if (indices.size() == 2)
        {
          std::array<size_t, 2> elem{indices[0], indices[1]};
          mesh.edges.push_back(elem);
        }
        else
        {
          throw std::runtime_error{std::string{"Invalid entry in connectivitiy file \""}.append(line).append("\"")};
        }
      }
    }
  }

  Mesh MeshName::load() const
  {
    Mesh mesh;
    readMainFile(mesh, filename(), dataname());
    auto connFile = connectivityfilename();
    if (boost::filesystem::exists(connFile))
    {
      readConnFile(mesh, connFile);
    }
    return mesh;
  }

  void MeshName::createDirectories() const
  {
    auto dir = fs::path(filename()).parent_path();
    if (!dir.empty())
    {
      fs::create_directories(dir);
    }
  }

  void MeshName::save(const Mesh &mesh) const
  {
    assert(mesh.positions.size() == mesh.data.size());

vtkSmartPointer<vtkUnstructuredGrid> unstructuredGrid = vtkSmartPointer<vtkUnstructuredGrid>::New();
vtkSmartPointer<vtkPoints> points = vtkSmartPointer<vtkPoints>::New();
vtkDoubleArray *data = vtkDoubleArray::New();
data->SetName("scalar");
data->SetNumberOfComponents(1);


  for (size_t i = 0; i < mesh.positions.size()-1; i++) {
    points->InsertNextPoint(mesh.positions[i][0], mesh.positions[i][1], mesh.positions[i][2]);
data->InsertNextTuple(&mesh.data[i]);
  }
  
unstructuredGrid->SetPoints(points);
unstructuredGrid->GetPointData()->AddArray(data);


  // Write file
  vtkSmartPointer<vtkUnstructuredGridWriter> writer = vtkSmartPointer<vtkUnstructuredGridWriter>::New();
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
    if (context.isParallel())
    {
      return {_bname + fs::path::preferred_separator + std::to_string(context.rank)};
    }
    else
    {
      return {_bname};
    }
  }

  std::vector<MeshName> BaseName::findAll(const ExecutionContext &context) const
  {
    if (!context.isParallel())
    {
      // Check single timestep/meshfiles first
      // Case: a single mesh
      if (fs::is_regular_file(_bname + ".vtk"))
      {
        return {MeshName{_bname}};
      }

      // Check multiple timesteps
      std::vector<MeshName> meshNames;
      for (int t = 0; true; ++t)
      {
        std::string stepMeshName = _bname + ".dt" + std::to_string(t);
        if (!fs::is_regular_file(stepMeshName + ".vtk"))
          break;
        meshNames.push_back(MeshName{stepMeshName});
      }
      std::cerr << "Names: " << meshNames.size() << '\n';
      return meshNames;
    }
    else
    {
      fs::path rank{std::to_string(context.rank)};
      // Is there a single partitioned mesh?
      if (fs::is_directory(_bname))
      {
        auto rankMeshName = (fs::path(_bname) / rank).string();
        if (fs::is_regular_file(rankMeshName + ".vtk"))
        {
          return {MeshName{rankMeshName}};
        }
      }

      // Check multiple timesteps
      std::vector<MeshName> meshNames;
      for (int t = 0; true; ++t)
      {
        fs::path stepDirectory{_bname + ".dt" + std::to_string(t)};
        auto rankMeshName = (stepDirectory / rank).string();
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
    oss << positions.size() << " Vertices, " << data.size() << " Data Points, " << edges.size() << " Edges, " << triangles.size() << " Triangles";
    return oss.str();
  }

  /// Creates a unique and element-wise ordered set of undirected edges.
  std::vector<Mesh::Edge> gather_unique_edges(const Mesh &mesh)
  {
    std::vector<Mesh::Edge> sorted;
    sorted.reserve(mesh.edges.size() + 3 * mesh.triangles.size());

    for (auto const &edge : mesh.edges)
    {
      const auto a = edge[0];
      const auto b = edge[1];
      sorted.push_back(Mesh::Edge{std::min(a, b), std::max(a, b)});
    }

    for (auto const &triangle : mesh.triangles)
    {
      const auto a = triangle[0];
      const auto b = triangle[1];
      const auto c = triangle[2];
      sorted.push_back(Mesh::Edge{std::min(a, b), std::max(a, b)});
      sorted.push_back(Mesh::Edge{std::min(a, c), std::max(a, c)});
      sorted.push_back(Mesh::Edge{std::min(b, c), std::max(b, c)});
    }
    std::sort(sorted.begin(), sorted.end(), EdgeCompare());
    auto end = std::unique(sorted.begin(), sorted.end());
    return std::vector<Mesh::Edge>(sorted.begin(), end);
  }

}
