#include <iostream>
#include <istream>
#include <fstream>
#include <string>
#include <boost/filesystem.hpp>
#include <mpi.h>
#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"
#include "utils/EventUtils.hpp"

#include "common.hpp"
namespace fs = boost::filesystem; 

/// Returns number n of directories meshname/0,1,2...n
int numMeshParts(std::string meshname)
{
  if (not fs::is_directory(meshname))
    throw std::runtime_error("Invalid mesh name: Directory not found. Directory Name: " + meshname);
  int i = 0;
  while (fs::exists(meshname + "/" + std::to_string(i)))
    i++;
  return i;
}

struct Mesh {
  std::vector<std::array<double, 3>> positions;
  std::vector<double> data;
};

/// Reads the mesh from the file. If not read_data, zeros are returned for data.
Mesh readMesh(std::istream& stream, bool read_data = true)
{
  Mesh mesh;
  double x, y, z, val;
  std::string line;
  while (std::getline(stream, line)){
    std::istringstream iss(line);
    iss >> x >> y >> z >> val; // split up by whitespace
    std::array<double, 3> vertexPos{x, y, z};
    mesh.positions.push_back(vertexPos);
    if (read_data) //val is ignored on B.
      mesh.data.push_back(val);
  }
  if (not read_data)
    mesh.data = std::vector<double>(mesh.positions.size(), 0);
  return mesh;
}

int main(int argc, char* argv[])
{
  MPI_Init(&argc, &argv);
  auto options = getOptions(argc, argv);
  bool verbose = options["verbose"].as<bool>();
  std::string meshname = options["mesh"].as<std::string>();
  std::string participant = options["participant"].as<std::string>();

  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

  auto numParts = numMeshParts(meshname + ".dt0");
  if (numParts < MPIsize)
    throw std::runtime_error("Mesh is too small for communicator, MeshSize="  + std::to_string(numParts)
                             + ", Comm_size=" + std::to_string(MPIsize));

  // Create and configure solver interface
  precice::SolverInterface interface(participant, MPIrank, MPIsize);
  interface.configure(options["precice-config"].as<std::string>());
  precice::utils::EventRegistry::instance().runName =  options["runName"].as<std::string>();
  
  int meshID = interface.getMeshID( (participant == "A") ? "MeshA" : "MeshB" ); // participant = A => MeshID = MeshA
  int dataID = interface.getDataID("Data", meshID);
  
  std::vector<int> vertexIDs;
  auto filename = meshname + ".dt1/" + std::to_string(MPIrank);
  std::ifstream infile(filename);
  // reads in mesh, 0 data for participant B
  auto mesh = readMesh(infile, participant == "A");
  infile.close();

  // Feed mesh to preCICE
  for (auto const & pos : mesh.positions)
    vertexIDs.push_back(interface.setMeshVertex(meshID, pos.data()));
  if (verbose) std::cout << "========= Rank " << MPIrank << " read in mesh of size " << vertexIDs.size() << std::endl;
    
  interface.initialize();

  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    if (verbose) std::cout << "Write initial data for participant " << participant << std::endl;
    interface.writeBlockScalarData(dataID, mesh.data.size(), vertexIDs.data(), mesh.data.data());
    interface.fulfilledAction(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  int round = 0;
  while (interface.isCouplingOngoing()) {
    if (participant == "A" and not mesh.data.empty()) {
      auto filename = meshname + ".dt" + std::to_string(round) + "/" + std::to_string(MPIrank);
      if (verbose) std::cout << "Read mesh for t=" << round << " from " << filename << std::endl;
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
        
    std::cout << "========= Write to " << outdir << std::endl;
    std::ofstream ostream((outdir / std::to_string(MPIrank)).string(), std::ios::trunc);
    ostream.precision(9);
    const auto& positions = mesh.positions;
    const auto& data = mesh.data;
    for (size_t i = 0; i < mesh.positions.size(); i++) {
      ostream << positions[i][0] << " " << positions[i][1] << " " << positions[i][2] << " " << data[i] << std::endl;
    }
    ostream.close();
  }

  MPI_Finalize();
}

