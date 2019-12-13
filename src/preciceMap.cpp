#include <iostream>
#include <fstream>
#include <string>
#include <boost/filesystem.hpp>
#include <mpi.h>
#include <precice/SolverInterface.hpp>
#include "prettyprint/prettyprint.hpp"
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

struct ScalarMesh {
  std::vector<std::array<double, 3>> positions;
  std::vector<double> data;
};

struct VectorMesh {
  std::vector<std::array<double, 3>> positions;
  std::vector<std::array<double, 3>> data;
};

/// Reads the mesh from the file. If not read_data, zeros are returned for data.
Mesh readMesh(std::istream& stream, bool read_data = true, int datadim=1)
{
  if (datadim==1){
    ScalarMesh mesh;
    double x, y, z, valx;
  }
  if (datadim == 3){
    VectorMesh mesh;
    double x, y, z, valx, valy, valz;
}

  std::string line;
  while (std::getline(stream, line)){
    std::istringstream iss(line);
    if (datadim == 1)
      iss >> x >> y >> z >> valx; // split up by whitespace
    if (datadim == 3) 
      iss >> x >> y >> z >> valx >> valy >> valz;
    std::array<double, 3> vertexPos{x, y, z};
    mesh.positions.push_back(vertexPos);
    if (read_data) // val is ignored on B.
      if (datadim==1)
        mesh.data.push_back(valx);
      if (datadim ==3)
        mesh.data.push
  }
  if (not read_data)
    mesh.data = std::vector<double>(mesh.positions.size(), 0);
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
  
  std::vector<int> vertexIDs;
  std::ifstream infile(meshes[0]);
  // reads in mesh, 0 data for participant B
  auto mesh = readMesh(infile, participant == "A");
  infile.close();

  // Feed mesh to preCICE
  for (auto const & pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));
  VLOG(1) << "Rank " << MPIrank << " read in mesh of size " << vertexIDs.size();
    
  interface.initialize();

  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    VLOG(1) << "Write initial data for participant " << participant;
    interface.writeBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
    interface.fulfilledAction(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  int round = 0;
  while (interface.isCouplingOngoing() and round < meshes.size()) {
    if (participant == "A" and not mesh.data.empty()) {
      auto filename = meshes[round];

      VLOG(1) << "Read mesh for t=" << round << " from " << filename;
      if (not boost::filesystem::exists(filename))
        throw std::runtime_error("File does not exist: " + filename);
      std::ifstream infile(filename);
      auto roundmesh = readMesh(infile, participant == "A");
      infile.close();
      interface.writeBlockScalarData(dataID, roundmesh.data.size(), vertexIDs.data(), roundmesh.data.data());
    }
    interface.advance(1);

    if (participant == "B") {
      interface.readBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
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
              << data[i] << std::endl;
    }
    ostream.close();
  }

  MPI_Finalize();
}

