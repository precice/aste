#pragma once

#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/filesystem/operations.hpp>

#include <mpi.h>

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

#include <algorithm>
#include <cassert>
#include <exception>
#include <fstream>
#include <iosfwd>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "logger.hpp"

namespace aste {

namespace fs = boost::filesystem;
class BaseName;
struct Mesh;
class MeshName;
struct MeshData;

class MeshException : public std::runtime_error {
public:
  MeshException(const std::string &what_arg)
      : std::runtime_error(what_arg){};
};
/**
 * @brief Information about current run MPI size and rank of the process
 *
 */
struct ExecutionContext {
  ExecutionContext() = default;
  ExecutionContext(int rank, int size)
      : rank(rank), size(size)
  {
    assert(0 <= rank && rank < size);
  };
  int  rank{0};
  int  size{1};
  bool isParallel() const
  {
    return size > 1;
  }
};

class MeshName {
public:
  MeshName(std::string meshname, std::string extension, const ExecutionContext &context)
      : _mname(std::move(meshname)), _ext(std::move(extension)), _context(context) {}

  std::string filename() const;

  void loadMesh(Mesh &mesh, const int dim, const bool requireConnectivity);
  void loadData(Mesh &mesh);
  void resetData(Mesh &mesh);
  void save(const Mesh &mesh, const std::string &outputFilename) const;

private:
  void createDirectories() const;

  std::string            _mname;
  std::string            _ext;
  const ExecutionContext _context;

  friend BaseName;
};

/**
 * @brief Whether data is read or write type
 *
 */
enum datatype { READ,
                WRITE,
                GRADIENT,
};
/**
 * @brief Information about data in mesh.
 * Contains whether data is write or read type
 * Number of components of data
 * Name of data
 * Data context (dataVector)
 * Data ID in preCICE
 */
struct MeshData {
  MeshData(datatype type, int numcomp, std::string name, int dataID)
      : type(type), numcomp(numcomp), name(std::move(name)), dataID(dataID){};
  MeshData(datatype type, int numcomp, std::string name, int dataID, int gradDimension)
      : type(type), numcomp(numcomp), name(std::move(name)), dataID(dataID), gradDimension(gradDimension){};

  datatype            type;
  int                 numcomp;
  std::string         name; // name of data
  std::vector<double> dataVector;
  int                 dataID;        // preCICE dataID
  int                 gradDimension; // Dimensions for gradient data
};

std::ostream &operator<<(std::ostream &out, const MeshName &mname);

class BaseName {
public:
  BaseName(std::string basename)
      : _bname(std::move(basename)) {}

  MeshName with(const ExecutionContext &context) const;

  std::vector<MeshName> findAll(const ExecutionContext &context) const;

private:
  std::string _bname;
};

/**
 * @brief Datastructure for storing meshes in ASTE
 *
 */
struct Mesh {
  using Vertex   = std::vector<double>;
  using VID      = std::vector<Vertex>::size_type;
  using Edge     = std::array<VID, 2>;
  using Triangle = std::array<VID, 3>;
  using Quad     = std::array<VID, 4>;
  using Tetra    = std::array<VID, 4>;
  std::vector<Vertex>   positions;
  std::vector<Edge>     edges;
  std::vector<Triangle> triangles;
  std::vector<Quad>     quadrilaterals;
  std::vector<Tetra>    tetrahedra;
  std::string           fname;
  std::vector<MeshData> meshdata;

  std::string previewData(std::size_t max = 10) const;
  std::string previewData(const MeshData &data, std::size_t max = 10) const;
  std::string summary() const;
};

struct EdgeCompare {
  bool operator()(const Mesh::Edge &lhs, const Mesh::Edge &rhs) const
  {
    return lhs[0] < rhs[0] || (lhs[0] == rhs[0] && lhs[1] < rhs[1]);
  }
};

std::vector<Mesh::Edge> gather_unique_edges(const Mesh &mesh);

} // namespace aste
