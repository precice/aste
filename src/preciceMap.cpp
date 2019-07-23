#include <iostream>
#include <fstream>
#include <string>
#include <boost/filesystem.hpp>
#include <boost/algorithm/string.hpp>
#include <mpi.h>
#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"
#include "utils/EventUtils.hpp"

#include "common.hpp"
#include "easylogging++.h"

INITIALIZE_EASYLOGGINGPP

namespace fs = boost::filesystem;


/// Returns list of meshes matching meshname or meshname.dtN for the given rank
std::vector<std::string> getMeshes(std::string basename, int rank)
{
  VLOG(1) << "Basename: " << basename;
  std::vector<std::string> meshes;
  if (fs::is_directory(basename)) {
    meshes.push_back(basename);
  }
  else {
    int t = 0;
    while (fs::is_directory(basename + ".dt" + std::to_string(t))) {
      meshes.push_back(basename + ".dt" + std::to_string(t));
      ++t;
    }
  }

  // add the rank number
  for (auto & mesh : meshes) {
    std::string rankFile = mesh + "/" + std::to_string(rank);
    if (fs::is_regular_file(rankFile))
      mesh = rankFile;
    else
      throw std::range_error("Mesh is not decomposed for requested rank, i.e. " + rankFile + " not found.");
  }
  
  LOG(DEBUG) << "Meshes: " << meshes;
  return meshes;
}

struct Mesh {
  std::vector<std::array<double, 3>> positions;
  std::vector<std::array<size_t, 2>> edges;
  std::vector<std::array<size_t, 3>> triangles;
  std::vector<double> data;
};


// Reads the main file containing the vertices and data
void readMainFile(Mesh& mesh, const std::string& filename, bool read_data)
{
    VLOG(1) << "Reading mesh vertices " << (read_data?"and data ":"") << "from file " << filename;
    std::ifstream mainFile{filename};
    std::string line;
    while (std::getline(mainFile, line)){
        double x, y, z, val;
        std::istringstream iss(line);
        iss >> x >> y >> z >> val; // split up by whitespace
        std::array<double, 3> vertexPos{x, y, z};
        mesh.positions.push_back(vertexPos);
        if (read_data) // val is ignored on B.
            mesh.data.push_back(val);
    }
    if (not read_data)
        mesh.data = std::vector<double>(mesh.positions.size(), 0);
}

// Reads the connectivity file containing the triangle and edge information
void readConnFile(Mesh& mesh, const std::string& filename)
{
    VLOG(1) << "Reading mesh connectivity information from file " << filename;
    std::ifstream connFile{filename};
    std::string line;
    while (std::getline(connFile, line)){
        std::vector<std::string> parts;
        boost::split(parts, line, [](char c){ return c == ' '; });
        std::vector<size_t> indices(parts.size());
        std::transform(parts.begin(), parts.end(), indices.begin(), [](const std::string& s) -> size_t {return std::stol(s);});

        if (indices.size() == 3) {
            std::array<size_t, 3> elem{indices[0], indices[1], indices[2]};
            mesh.triangles.push_back(elem);
        } else if (indices.size() == 2) {
            std::array<size_t, 2> elem{indices[0], indices[1]};
            mesh.edges.push_back(elem);
        } else {
            throw std::runtime_error{"Invalid entry in connectivitiy file"};
        }
    }
}

/// Reads the mesh from the file. If not read_data, zeros are returned for data.
Mesh readMesh(const std::string& filename, bool read_data = true)
{
  Mesh mesh;
  readMainFile(mesh, filename, read_data);
  std::string connFile = boost::filesystem::path(filename).replace_extension(".conn.txt").string();
  if (boost::filesystem::exists(connFile)) {
    readConnFile(mesh, connFile);
  } else {
    VLOG(1) << "Skipped Reading mesh connectivity information from non-existent file " << filename;
  }
  return mesh;
}

int main(int argc, char* argv[])
{
  START_EASYLOGGINGPP(argc, argv);
  MPI_Init(&argc, &argv);
  auto options = getOptions(argc, argv);
  std::string meshname = options["mesh"].as<std::string>();
  std::string participant = options["participant"].as<std::string>();

  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

  auto meshes = getMeshes(meshname, MPIrank);

  // Create and configure solver interface
  precice::SolverInterface interface(participant, MPIrank, MPIsize);
  interface.configure(options["precice-config"].as<std::string>());
  precice::utils::EventRegistry::instance().runName =  options["runName"].as<std::string>();
  
  int meshID = interface.getMeshID( (participant == "A") ? "MeshA" : "MeshB" ); // participant = A => MeshID = MeshA
  int dataID = interface.getDataID("Data", meshID);
  
  // reads in mesh, 0 data for participant B
  auto mesh = readMesh(meshes[0], participant == "A");
  VLOG(1) << "The mesh contains:\n " << mesh.positions.size() << " Vertices\n " << mesh.data.size() << " Data\n " << mesh.edges.size()  << " Edges\n " << mesh.triangles.size() << " Triangles";

  // Feed vertices to preCICE
  std::vector<int> vertexIDs;
  vertexIDs.resize(mesh.positions.size());
  for (auto const & pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));
  VLOG(1) << "Rank " << MPIrank << " read in mesh of size " << vertexIDs.size();

  for (auto const & edge : mesh.edges)
      interface.setMeshEdge(
              meshID,
              vertexIDs.at(edge[0]),
              vertexIDs.at(edge[1])
              );

  for (auto const & triangle : mesh.triangles)
      interface.setMeshTriangleWithEdges(
              meshID,
              vertexIDs.at(triangle[0]),
              vertexIDs.at(triangle[1]),
              vertexIDs.at(triangle[2])
              );
    
  interface.initialize();

  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    VLOG(1) << "Write initial data for participant " << participant;
    interface.writeBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
    std::ostringstream oss;
    for(size_t i = 0; i<std::min((size_t)10, mesh.data.size()); ++i)
        oss << mesh.data[i] << ' ';
    VLOG(1) << "Data written: " << oss.str();

    interface.fulfilledAction(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  size_t round = 0;
  while (interface.isCouplingOngoing() and round < meshes.size()) {
    if (participant == "A" and not mesh.data.empty()) {
      auto filename = meshes[round];

      VLOG(1) << "Read mesh for t=" << round << " from " << filename;
      if (not boost::filesystem::exists(filename))
        throw std::runtime_error("File does not exist: " + filename);
      auto roundmesh = readMesh(filename, participant == "A");
      VLOG(1) << "This roundmesh contains:\n " << roundmesh.positions.size() << " Vertices\n " << roundmesh.data.size() << " Data\n " << roundmesh.edges.size()  << " Edges\n " << roundmesh.triangles.size() << " Triangles";
      assert(roundmesh.data.size() == vertexIDs.size());
      interface.writeBlockScalarData(dataID, roundmesh.data.size(), vertexIDs.data(), roundmesh.data.data());
    std::ostringstream oss;
    for(size_t i = 0; i<std::min((size_t)10, mesh.data.size()); ++i)
        oss << roundmesh.data[i] << ' ';
    VLOG(1) << "Data written: " << oss.str();
    }
    interface.advance(1);

    if (participant == "B") {
      interface.readBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
      std::ostringstream oss;
      for(size_t i = 0; i<std::min((size_t)10, mesh.data.size()); ++i)
          oss << mesh.data[i] << ' ';
      VLOG(1) << "Data read: " << oss.str();
    }
    round++;
  }

  interface.finalize();
    
  // Write out results in same format as data was read
  if (participant == "B") {
    fs::path outdir(options["output"].as<std::string>());
    if (MPIrank == 0) {
      fs::remove_all(outdir);
      fs::create_directory(outdir);
    }
    MPI_Barrier(MPI_COMM_WORLD);
        
    VLOG(1) << "Writing results to " << outdir;
    std::ofstream ostream((outdir / std::to_string(MPIrank)).string(), std::ios::trunc);
    ostream.precision(9);
    auto const & positions = mesh.positions;
    auto const & data = mesh.data;
    for (size_t i = 0; i < mesh.positions.size(); i++) {
      ostream << positions[i][0] << " "
              << positions[i][1] << " "
              << positions[i][2] << " "
              << data[i] << '\n';
    }
    ostream.close();
  }

  MPI_Finalize();
}

