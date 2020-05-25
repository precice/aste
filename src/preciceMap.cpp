#include <string>
#include <boost/filesystem.hpp>
#include <boost/container/flat_map.hpp>
#include <mpi.h>
#include "precice/SolverInterface.hpp"
//#include "utils/EventUtils.hpp"
#include <algorithm>
#include <cassert>
#include <functional>
#include <exception>

#include "common.hpp"
#include "easylogging++.h"
#include "mesh.hpp"
#include <chrono>

INITIALIZE_EASYLOGGINGPP

namespace fs = boost::filesystem;

using VertexID = int;
using EdgeID = int;

struct Edge {
    Edge(VertexID a, VertexID b) : vA(std::min(a,b)), vB(std::max(a,b)) {}
    VertexID vA;
    VertexID vB;
};

bool operator==(const Edge& lhs, const Edge& rhs) {
    return (lhs.vA == rhs.vA) && (lhs.vB == rhs.vB);
}

bool operator<(const Edge& lhs, const Edge& rhs) {
    return (lhs.vA < rhs.vA) || ( (lhs.vA == rhs.vA) && (lhs.vB < rhs.vB) );
}

namespace std {
    template<> struct hash<Edge> {
        using argument_type = Edge;
        using result_type = std::size_t;
        result_type operator()(argument_type const& e) const noexcept {
            return std::hash<int>{}(e.vA) ^ std::hash<int>{}(e.vB);
        }
    };
};

aste::ExecutionContext initializeMPI(int argc, char* argv[]) {
  MPI_Init(&argc, &argv);
  int rank = 0, size = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  return {rank, size};
}

std::vector<int> setupMesh(precice::SolverInterface& interface, const aste::Mesh& mesh, int meshID) {
  auto tstart = std::chrono::steady_clock::now();

  VLOG(1) << "Mesh Setup: 1) Vertices";
  // Feed vertices to preCICE
  std::vector<int> vertexIDs;
  vertexIDs.reserve(mesh.positions.size());
  for (auto const & pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));

  auto tconnectivity = std::chrono::steady_clock::now();

  boost::container::flat_map<Edge, EdgeID> edgeMap;
  edgeMap.reserve(mesh.edges.size() + 2*mesh.triangles.size());

  VLOG(1) << "Mesh Setup: 2) Explicit Edges";
  for (auto const & edge : mesh.edges) {
      const auto a = vertexIDs.at(edge[0]);
      const auto b = vertexIDs.at(edge[1]);
      assert(a != b);

      auto iter = edgeMap.find(Edge{a, b});
      if (iter == edgeMap.end()) {
          EdgeID eid = interface.setMeshEdge(meshID, a, b);
          edgeMap.emplace(Edge{a, b}, eid);
      }
  }

  VLOG(1) << "Mesh Setup: 3) Implicit Edges";
  for (auto const & triangle : mesh.triangles) {
      const auto a = vertexIDs.at(triangle[0]);
      const auto b = vertexIDs.at(triangle[1]);
      const auto c = vertexIDs.at(triangle[2]);
      assert(a != b);
      assert(b != c);
      assert(c != a);

      const Edge ab{a, b};
      auto ab_pos = edgeMap.find(ab);
      if (ab_pos == edgeMap.end()) {
          EdgeID eid = interface.setMeshEdge(meshID, a, b);
          edgeMap.emplace(ab, eid);
      }
      const Edge bc{b, c};
      auto bc_pos = edgeMap.find(bc);
      if (bc_pos == edgeMap.end()) {
          EdgeID eid = interface.setMeshEdge(meshID, b, c);
          edgeMap.emplace(bc, eid);
      }
      const Edge ca{c, a};
      auto ca_pos = edgeMap.find(ca);
      if (ca_pos == edgeMap.end()) {
          EdgeID eid = interface.setMeshEdge(meshID, c, a);
          edgeMap.emplace(ca, eid);
      }
  }

  VLOG(1) << "Mesh Setup: 4) Triangles";
  for (auto const & triangle : mesh.triangles) {
      const auto a = vertexIDs[triangle[0]];
      const auto b = vertexIDs[triangle[1]];
      const auto c = vertexIDs[triangle[2]];

      interface.setMeshTriangle( meshID, 
              edgeMap[Edge{a,b}],
              edgeMap[Edge{b,c}],
              edgeMap[Edge{c,a}]
              );
  }
  auto tend = std::chrono::steady_clock::now();

  VLOG(1)
    << "Mesh Setup Took "
    << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tstart).count() << "ms ("
    << std::chrono::duration_cast<std::chrono::milliseconds>(tconnectivity - tstart).count() << "ms for vertices, "
    << std::chrono::duration_cast<std::chrono::milliseconds>(tend - tconnectivity).count() << "ms for connectivity)";
  return vertexIDs;
}


int main(int argc, char* argv[])
{
  START_EASYLOGGINGPP(argc, argv);
  auto context = initializeMPI(argc, argv);
  auto options = getOptions(argc, argv);
  const std::string meshname = options["mesh"].as<std::string>();
  const std::string participant = options["participant"].as<std::string>();

  auto meshes = aste::BaseName(meshname).findAll(context);
  if (meshes.empty()) {
    throw std::invalid_argument("ERROR: Could not find meshes for name: " + meshname);
  }

  // Create and configure solver interface
  precice::SolverInterface interface(participant, options["precice-config"].as<std::string>(), context.rank, context.size);
  //precice::utils::EventRegistry::instance().runName =  options["runName"].as<std::string>();
  
  const int meshID = interface.getMeshID( (participant == "A") ? "MeshA" : "MeshB" ); // participant = A => MeshID = MeshA
  const int dataID = interface.getDataID("Data", meshID);
  
  // reads in mesh, 0 data for participant B
  auto mesh = meshes[0].load();
  VLOG(1) << "The mesh contains: " << mesh.summary();

  std::vector<int> vertexIDs = setupMesh(interface, mesh, meshID);
  VLOG(1) << "Mesh setup completed on Rank " << context.rank;
    
  interface.initialize();

  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    VLOG(1) << "Write initial data for participant " << participant;
    interface.writeBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
    VLOG(1) << "Data written: " << mesh.previewData();

    interface.markActionFulfilled(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  size_t round = 0;
  while (interface.isCouplingOngoing() and round < meshes.size()) {
    if (participant == "A") {
      VLOG(1) << "Read mesh for t=" << round << " from " << meshes[round];
      auto roundmesh = meshes[round].load();
      VLOG(1) << "This roundmesh contains: " << roundmesh.summary();
      assert(roundmesh.data.size() == vertexIDs.size());
      interface.writeBlockScalarData(dataID, roundmesh.data.size(), vertexIDs.data(), roundmesh.data.data());
      VLOG(1) << "Data written: " << mesh.previewData();
    }
    interface.advance(1);

    if (participant == "B") {
      interface.readBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
      VLOG(1) << "Data read: " << mesh.previewData();
    }
    round++;
  }

  interface.finalize();
    
  // Write out results in same format as data was read
  if (participant == "B") {
    auto meshName = aste::BaseName{options["output"].as<std::string>()}.with(context);
    auto filename = fs::path(meshName.filename());
    if (context.rank == 0) {
      auto dir = filename.parent_path();
      fs::remove_all(dir);
      fs::create_directory(dir);
    }
    MPI_Barrier(MPI_COMM_WORLD);
        
    VLOG(1) << "Writing results to " << filename;
    meshName.save(mesh);
  }

  MPI_Finalize();
}

