#pragma once

#include <algorithm>
#include <boost/container/flat_map.hpp>
#include <boost/container/flat_set.hpp>
#include <boost/filesystem.hpp>
#include <cassert>
#include <chrono>
#include <exception>
#include <functional>
#include <iostream>
#include <mpi.h>
#include <string>
#include "common.hpp"
#include "configreader.hpp"
#include "easylogging++.h"
#include "mesh.hpp"
#include "modes.hpp"
#include "precice/SolverInterface.hpp"

namespace fs = boost::filesystem;

using VertexID = int;
using EdgeID   = int;

struct Edge {
  Edge(VertexID a, VertexID b)
      : vA(std::min(a, b)), vB(std::max(a, b)) {}
  VertexID vA;
  VertexID vB;
};

using EdgeIdMap = boost::container::flat_map<Edge, EdgeID>;

namespace aste {
aste::ExecutionContext initializeMPI(int argc, char *argv[]);

std::vector<int> setupVertexIDs(precice::SolverInterface &interface,
                                const aste::Mesh &mesh, int meshID);

EdgeIdMap        setupEdgeIDs(precice::SolverInterface &interface, const aste::Mesh &mesh, int meshID, const std::vector<int> &vertexIDs);
std::vector<int> setupMesh(precice::SolverInterface &interface, const aste::Mesh &mesh, int meshID);
} // namespace aste
