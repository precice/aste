#include <string>
#include <cmath>
#include <iostream>
#include <mpi.h>

#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"

#include "common.hpp"


using std::cout;
using std::endl;


Mesh getMyMesh(OptionMap options, int MPIrank, int MPIsize)
{
  double xSize = options["x"].as<double>();
  double ySize = options["y"].as<double>();
  int nx =  options["nx"].as<int>();
  int ny =  options["ny"].as<int>();
  double xInc = xSize / nx;
  double yInc = ySize / ny;

  Mesh mesh;
  for (double x = 0; x < xSize; x+= xInc) {
    for (double y = 0; y < ySize; y+= yInc) {
      Vertex v = { x*xInc, y*yInc};
      mesh.push_back(v);
    }
  }

  return partition(mesh, MPIsize)[MPIrank];
}


/// Fills a vector with data values
std::vector<double> getData(Mesh& mesh)
{
  std::vector<double> data;
  for (auto &v : mesh) {
    data.emplace_back(v[0] + v[1]);
  }
  return data;
}


int main(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);

  OptionMap options = getOptions(argc, argv);
  printOptions(options);
  std::string participant = options["participant"].as<std::string>();
  
  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

  precice::SolverInterface interface(participant, MPIrank, MPIsize);
  interface.configure(options["precice-config"].as<std::string>());
  int meshID = interface.getMeshID(options["mesh"].as<std::string>());
  int dataID = interface.getDataID(options["data"].as<std::string>(), meshID);

  Mesh mesh = getMyMesh(options, MPIrank, MPIsize);
  auto data = getData(mesh);
  cout << mesh << endl;
  cout << data << endl;
  std::vector<int> vertexIDs;
  
  size_t localN = mesh.size();
  for (size_t i = 0; i < localN; i++) {
    vertexIDs.push_back(interface.setMeshVertex(meshID, static_cast<const double *>(mesh[i].data())));
  }
  
  interface.initialize();

  cout << "INITALIZED!!" << endl;
  
  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    interface.writeBlockScalarData(dataID, localN, vertexIDs.data(), data.data());
    cout << "Wrote initial data = " << data << endl;
    interface.fulfilledAction(precice::constants::actionWriteInitialData());
    interface.initializeData();
  }

  while (interface.isCouplingOngoing()) {
    interface.writeBlockScalarData(dataID, localN, vertexIDs.data(), data.data());

    interface.advance(1);
    
    interface.readBlockScalarData(dataID, localN, vertexIDs.data(), data.data());
  }
  interface.finalize();


  
  MPI_Finalize();

  return 0;
}
