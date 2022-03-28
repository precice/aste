#include <boost/container/flat_map.hpp>
#include <boost/container/flat_set.hpp>
#include <boost/filesystem.hpp>
#include <mpi.h>
#include <string>
#include "precice/SolverInterface.hpp"
//#include "utils/EventUtils.hpp"
#include <algorithm>
#include <cassert>
#include <exception>
#include <functional>

#include <chrono>
#include "common.hpp"
#include "easylogging++.h"
#include "mesh.hpp"

INITIALIZE_EASYLOGGINGPP

namespace fs = boost::filesystem;

using VertexID = int;
using EdgeID   = int;

struct Edge {
  Edge(VertexID a, VertexID b)
      : vA(std::min(a, b)), vB(std::max(a, b)) {}
  VertexID vA;
  VertexID vB;
};

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

aste::ExecutionContext initializeMPI(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);
  int rank = 0, size = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  return {rank, size};
}

std::vector<int> setupVertexIDs(precice::SolverInterface &interface,
                                const aste::Mesh &mesh, int meshID)
{
#ifdef ASTE_SET_MESH_BLOCK
  const auto          nvertices = mesh.positions.size();
  std::vector<double> posData(3 * nvertices);
  for (unsigned long i = 0; i < nvertices; ++i) {
    const auto &pos = mesh.positions[i];
    std::copy(pos.begin(), pos.end(), &posData[i * 3]);
  }

  std::vector<int> vertexIDs(nvertices);
  interface.setMeshVertices(meshID, nvertices, posData.data(), vertexIDs.data());
  return vertexIDs;
#else
  std::vector<int> vertexIDs;
  vertexIDs.reserve(mesh.positions.size());
  for (auto const &pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));
  return vertexIDs;
#endif
}

using EdgeIdMap = boost::container::flat_map<Edge, EdgeID>;

EdgeIdMap setupEdgeIDs(precice::SolverInterface &interface, const aste::Mesh &mesh, int meshID, const std::vector<int> &vertexIDs)
{
  VLOG(1) << "Mesh Setup: 2.1) Gather Unique Edges";
  const auto unique_edges{gather_unique_edges(mesh)};

  VLOG(1) << "Mesh Setup: 2.2) Register Edges";
  boost::container::flat_map<Edge, EdgeID> edgeMap;
  edgeMap.reserve(unique_edges.size());

  for (auto const &edge : unique_edges) {
    const auto a = vertexIDs.at(edge[0]);
    const auto b = vertexIDs.at(edge[1]);
    assert(a != b);
    EdgeID eid = interface.setMeshEdge(meshID, a, b);
    edgeMap.emplace_hint(edgeMap.end(), Edge{a, b}, eid);
  }
  return edgeMap;
}

std::vector<int> setupMesh(precice::SolverInterface &interface, const aste::Mesh &mesh, int meshID)
{
  auto tstart = std::chrono::steady_clock::now();

  VLOG(1) << "Mesh Setup: 1) Vertices";
  const auto vertexIDs = setupVertexIDs(interface, mesh, meshID);

  auto tconnectivity = std::chrono::steady_clock::now();
  VLOG(1) << "Mesh Setup: 2) Edges";
  const auto edgeMap = setupEdgeIDs(interface, mesh, meshID, vertexIDs);

  VLOG(1) << "Mesh Setup: 3) Triangles";
  for (auto const &triangle : mesh.triangles) {
    const auto a = vertexIDs[triangle[0]];
    const auto b = vertexIDs[triangle[1]];
    const auto c = vertexIDs[triangle[2]];

    interface.setMeshTriangle(meshID,
                              edgeMap.at(Edge{a, b}),
                              edgeMap.at(Edge{b, c}),
                              edgeMap.at(Edge{c, a}));
  }

  VLOG(1) << "Mesh Setup: 4) Quadrilaterals";
  for (auto const &quadrilateral : mesh.quadrilaterals) {
    const auto a = vertexIDs[quadrilateral[0]];
    const auto b = vertexIDs[quadrilateral[1]];
    const auto c = vertexIDs[quadrilateral[2]];
    const auto d = vertexIDs[quadrilateral[3]];

    interface.setMeshQuad(meshID,
                          edgeMap.at(Edge{a, b}),
                          edgeMap.at(Edge{b, c}),
                          edgeMap.at(Edge{c, d}),
                          edgeMap.at(Edge{d, a}));
  }

  auto tend = std::chrono::steady_clock::now();

  VLOG(1)
      << "Mesh Setup Took "
      << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tstart).count() << "ms ("
      << std::chrono::duration_cast<std::chrono::milliseconds>(tconnectivity - tstart).count() << "ms for vertices, "
      << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tconnectivity).count() << "ms for connectivity)";
  return vertexIDs;
}

int main(int argc, char *argv[])
{
  START_EASYLOGGINGPP(argc, argv);
  auto              context     = initializeMPI(argc, argv);
  auto              options     = getOptions(argc, argv);
  const std::string meshname    = options["mesh"].as<std::string>();
  const std::string participant = options["participant"].as<std::string>();
  const std::string dataname    = options["data"].as<std::string>();
  const bool        isVector    = options["vector"].as<bool>();

  // gradient data
  const bool withGradient = options["gradient"].as<bool>();


  auto meshes = aste::BaseName(meshname).findAll(context);
  if (meshes.empty()) {
    throw std::invalid_argument("ERROR: Could not find meshes for name: " + meshname);
  }

  // Create and configure solver interface
  precice::SolverInterface interface(participant, options["precice-config"].as<std::string>(), context.rank, context.size);

  // Get dimension/components of data
  const int dim = isVector ? interface.getDimensions() : 1;

  const int meshID = interface.getMeshID((participant == "A") ? "MeshA" : "MeshB"); // participant = A => MeshID = MeshA
  const int dataID = interface.getDataID("Data", meshID);

  VLOG(1) << "Loading mesh from " << meshes.front().filename();
  // reads in mesh, 0 data for participant B
  auto mesh = meshes.front().load(dim, dataname, withGradient);
  VLOG(1) << "The mesh contains: " << mesh.summary();

  std::vector<int> vertexIDs = setupMesh(interface, mesh, meshID);
  VLOG(1) << "Mesh setup completed on Rank " << context.rank;

  // gradient data
  //const bool withGradient = mesh.data.hasGradient();

  interface.initialize();

  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    VLOG(1) << "Write initial data for participant " << participant;
    if (isVector) {
      assert(mesh.data.size() == vertexIDs.size() * dim);
      interface.writeBlockVectorData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.data.data());

      //TODO: WRITE GRADIENT DATA IF NECESSARY
      if(withGradient) {
        //interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.gradientdx.data(), mesh.gradientdy.data(), mesh.gradientdz.data());
        interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.gradientData.data(), true);
      }

    } else {
      assert(mesh.data.size() == vertexIDs.size());
      interface.writeBlockScalarData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.data.data());

      //TODO: WRITE GRADIENT DATA IF NECESSARY
      if(withGradient) {
        //interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.gradientdx.data(), mesh.gradientdy.data(), mesh.gradientdz.data());
        interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.gradientData.data(), true);
      }

    }
    VLOG(1) << "Data written: " << mesh.previewData();

    interface.markActionFulfilled(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  size_t round = 0;
  while (interface.isCouplingOngoing() and round < meshes.size()) {

    if (participant == "A") {
      VLOG(1) << "Read mesh for t=" << round << " from " << meshes[round];
      auto roundmesh = meshes[round].load(dim, dataname, withGradient);
      VLOG(1) << "This roundmesh contains: " << roundmesh.summary();
      if (isVector) {
        assert(roundmesh.data.size() == vertexIDs.size() * dim);
        interface.writeBlockVectorData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.data.data());

        //TODO: WRITE GRADIENT DATA IF NECESSARY
        if(withGradient) {
          //interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.gradientdx.data(), roundmesh.gradientdy.data(), roundmesh.gradientdz.data());
          interface.writeBlockVectorGradientData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.gradientData.data(), true);
        }

      } else {
        assert(roundmesh.data.size() == vertexIDs.size());
        interface.writeBlockScalarData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.data.data());

        //TODO: WRITE GRADIENT DATA IF NECESSARY
        if(withGradient) {
          //interface.writeBlockScalarGradientData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.gradientdx.data(), roundmesh.gradientdy.data(), roundmesh.gradientdz.data());
          interface.writeBlockScalarGradientData(dataID, vertexIDs.size(), vertexIDs.data(), roundmesh.gradientData.data(),true );
        }

      }
      VLOG(1) << "Data written: " << mesh.previewData();
    }
    interface.advance(1);

    if (participant == "B") {
      if (isVector) {
        interface.readBlockVectorData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.data.data());
      } else {
        interface.readBlockScalarData(dataID, vertexIDs.size(), vertexIDs.data(), mesh.data.data());
      }
      VLOG(1) << "Data read: " << mesh.previewData();
    }
    round++;
  }

  interface.finalize();

  // Write out results in same format as data was read
  if (participant == "B") {
    auto meshName = aste::BaseName{options["output"].as<std::string>()}.with(context);
    auto filename = fs::path(meshName.filename());
    if (context.rank == 0 && fs::exists(filename)) {
      if (context.isParallel()) {
        // Remove the directory <meshName>/<rank>.txt
        auto dir = filename.parent_path();
        if (!dir.empty()) {
          fs::remove_all(dir);
          fs::create_directory(dir);
        }
      } else {
        // Remove the mesh file <meshName>.txt
        fs::remove(filename);
      }
    }
    MPI_Barrier(MPI_COMM_WORLD);

    VLOG(1) << "Writing results to " << filename;
    meshName.save(mesh, dataname, withGradient);
  }

  MPI_Finalize();
  return EXIT_SUCCESS;
}
