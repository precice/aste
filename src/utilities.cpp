#include "utilities.hpp"

bool operator==(const Edge &lhs, const Edge &rhs)
{
  return (lhs.vA == rhs.vA) && (lhs.vB == rhs.vB);
}

bool operator<(const Edge &lhs, const Edge &rhs)
{
  return (lhs.vA < rhs.vA) || ((lhs.vA == rhs.vA) && (lhs.vB < rhs.vB));
}

namespace std {
template <>
struct hash<Edge> {
  using argument_type = Edge;
  using result_type   = std::size_t;
  result_type operator()(argument_type const &e) const noexcept
  {
    return std::hash<int>{}(e.vA) ^ std::hash<int>{}(e.vB);
  }
};
}; // namespace std

aste::ExecutionContext aste::initializeMPI(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);
  int rank = 0;
  int size = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  return {rank, size};
}

std::vector<int> aste::setupVertexIDs(precice::Participant &interface,
                                      const aste::Mesh &mesh, const std::string &meshName)
{
#ifdef ASTE_SET_MESH_BLOCK
  const auto          dimension = interface.getMeshDimensions(meshName);
  const auto          nvertices = mesh.positions.size();
  std::vector<double> posData(dimension * nvertices);
  for (unsigned long i = 0; i < nvertices; ++i) {
    const auto &pos = mesh.positions[i];
    assert(pos.size() == static_cast<unsigned int>(dimension));
    std::copy(pos.begin(), pos.end(), &posData[i * dimension]);
  }

  std::vector<int> vertexIDs(nvertices);
  interface.setMeshVertices(meshName, posData, vertexIDs);
  return vertexIDs;
#else
  std::vector<int> vertexIDs;
  vertexIDs.reserve(mesh.positions.size());
  for (auto const &pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));
  return vertexIDs;
#endif
}

void aste::setupEdgeIDs(precice::Participant &interface, const aste::Mesh &mesh, const std::string &meshName, const std::vector<int> &vertexIDs)
{
  ASTE_DEBUG << "Mesh Setup: 2.1) Gather Unique Edges";
  const auto unique_edges{gather_unique_edges(mesh)};

  ASTE_DEBUG << "Mesh Setup: 2.2) Register Edges";

  for (auto const &edge : unique_edges) {
    const auto a = vertexIDs.at(edge[0]);
    const auto b = vertexIDs.at(edge[1]);
    assert(a != b);
    interface.setMeshEdge(meshName, a, b);
  }
}

std::vector<double> aste::setupDirectMeshAccess(precice::Participant &interface, const aste::Mesh &mesh, const std::string &meshName, const aste::ExecutionContext &exec)
{
  ASTE_DEBUG << "Setting up direct access for: " << meshName;
  ASTE_DEBUG << "Setting up coordinates vector for mesh...";

  const auto          dim       = interface.getMeshDimensions(meshName);
  const auto          nvertices = mesh.positions.size();
  std::vector<double> coordinates(dim * nvertices);
  for (unsigned long i = 0; i < nvertices; ++i) {
    const auto &pos = mesh.positions[i];
    assert(pos.size() == static_cast<unsigned int>(dim));
    std::copy(pos.begin(), pos.end(), &coordinates[i * dim]);
  }

  ASTE_DEBUG << "Computing the (rank-local) bounding box:";

  std::vector<double> bb(2 * dim);

  // for parallel runs, we define a proper bounding box
  if (exec.isParallel()) {
    // Initialize min and max values
    for (int i = 0; i < dim; ++i) {
      bb[2 * i]     = std::numeric_limits<double>::max();    // min values
      bb[2 * i + 1] = std::numeric_limits<double>::lowest(); // max values
    }

    // Iterate through the coordinates
    for (size_t i = 0; i < coordinates.size(); i += dim) {
      for (int j = 0; j < dim; ++j) {
        double coord  = coordinates[i + j];
        bb[2 * j]     = std::min(coord - 1e-12, bb[2 * j]);     // Update min
        bb[2 * j + 1] = std::max(coord + 1e-12, bb[2 * j + 1]); // Update max
      }
    }
  } else {
    // for serial runs, we just take everything (to account for potential discretization imbalances)
    for (int i = 0; i < dim; ++i) {
      bb[2 * i]     = std::numeric_limits<double>::lowest(); // min values
      bb[2 * i + 1] = std::numeric_limits<double>::max();    // max values
    }
  }
  interface.setMeshAccessRegion(meshName, bb);
  return coordinates;
}

std::vector<int> aste::setupMesh(precice::Participant &interface, const aste::Mesh &mesh, const std::string &meshName)
{
  auto tstart = std::chrono::steady_clock::now();

  ASTE_DEBUG << "Mesh Setup started for mesh: " << mesh.fname;
  ASTE_DEBUG << "Mesh Setup: 1) Vertices";
  const auto vertexIDs = setupVertexIDs(interface, mesh, meshName);

  auto tconnectivity = std::chrono::steady_clock::now();

  if (interface.requiresMeshConnectivityFor(meshName)) {
    ASTE_DEBUG << "Mesh Setup: 2) Edges";
    setupEdgeIDs(interface, mesh, meshName, vertexIDs);
    // ASTE_DEBUG << "Total " << edgeMap.size() << " edges are configured";
    if (!mesh.triangles.empty()) {
      ASTE_DEBUG << "Mesh Setup: 3) " << mesh.triangles.size() << " Triangles";
      for (auto const &triangle : mesh.triangles) {
        const auto a = vertexIDs[triangle[0]];
        const auto b = vertexIDs[triangle[1]];
        const auto c = vertexIDs[triangle[2]];

        interface.setMeshTriangle(meshName, a, b, c);
      }
    } else {
      ASTE_DEBUG << "Mesh Setup: 3) No Triangles are found/required. Skipped";
    }
    if (!mesh.quadrilaterals.empty()) {
      ASTE_DEBUG << "Mesh Setup: 4) " << mesh.quadrilaterals.size() << " Quadrilaterals";
      for (auto const &quadrilateral : mesh.quadrilaterals) {
        const auto a = vertexIDs[quadrilateral[0]];
        const auto b = vertexIDs[quadrilateral[1]];
        const auto c = vertexIDs[quadrilateral[2]];
        const auto d = vertexIDs[quadrilateral[3]];

        interface.setMeshQuad(meshName, a, b, c, d);
      }
    } else {
      ASTE_DEBUG << "Mesh Setup: 4) No Quadrilaterals are found/required. Skipped";
    }

#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
    if (!mesh.tetrahedra.empty()) {
      ASTE_DEBUG << "Mesh Setup: 5) " << mesh.tetrahedra.size() << " Tetrahedra";
      for (auto const &tetra : mesh.tetrahedra) {
        const auto a = vertexIDs[tetra[0]];
        const auto b = vertexIDs[tetra[1]];
        const auto c = vertexIDs[tetra[2]];
        const auto d = vertexIDs[tetra[3]];

        interface.setMeshTetrahedron(meshName, a, b, c, d);
      }
    } else {
      ASTE_DEBUG << "Mesh Setup: 5) No Tetrahedra are found/required. Skipped";
    }
#else
    ASTE_DEBUG << "Mesh Setup: 5) Tetrahedra support was disabled.";
#endif
  } else {
    ASTE_DEBUG << "Mesh Setup: 2) Skipped connectivity information on mesh \"" << mesh.fname << "\" as it is not required.";
  }
  auto tend = std::chrono::steady_clock::now();

  ASTE_DEBUG
      << "Mesh Setup Took "
      << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tstart).count() << "ms ("
      << std::chrono::duration_cast<std::chrono::milliseconds>(tconnectivity - tstart).count() << "ms for vertices, "
      << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tconnectivity).count() << "ms for connectivity)";
  return vertexIDs;
}
