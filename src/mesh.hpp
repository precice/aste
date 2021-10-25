#pragma once

#include <boost/filesystem.hpp>
#include <cassert>
#include <exception>
#include <iosfwd>
#include <string>
#include <vector>

namespace aste {

namespace fs = boost::filesystem;
class BaseName;
struct Mesh;
class MeshName;

class MeshException : public std::runtime_error {
public:
  MeshException(const std::string &what_arg)
      : std::runtime_error(what_arg){};
};

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
  MeshName() = default;

  std::string filename() const;

  Mesh load(const int &dim, const std::string &dataname) const;

  void save(const Mesh &mesh, const std::string &dataname) const;

private:
  MeshName(std::string meshname)
      : _mname(std::move(meshname)) {}

  void createDirectories() const;

  std::string _mname;

  friend BaseName;
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

struct Mesh {
  using Vertex   = std::array<double, 3>;
  using Edge     = std::array<int, 2>;
  using Triangle = std::array<int, 3>;
  using Quad     = std::array<int, 4>;
  std::vector<Vertex>   positions;
  std::vector<Edge>     edges;
  std::vector<Triangle> triangles;
  std::vector<Quad>     quadrilaterals;
  std::vector<double>   data;

  std::string previewData(std::size_t max = 10) const;
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
