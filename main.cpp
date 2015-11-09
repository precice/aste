#include <string>
#include <cmath>
#include <iostream>
#include <mpi.h>

#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"

#include "common.hpp"
#include <functional>
#include <random>


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
Data getData(Mesh& mesh)
{
  std::random_device rd;
  std::mt19937 mt(rd());
  std::uniform_real_distribution<double> dist(0.0, 1.0);
  auto real_rand = std::bind(dist, mt);
  
  Data data;
  for (auto &v : mesh) {
    //data.emplace_back(v[0] + v[1]);
    data.emplace_back(real_rand());
  }
  return data;
}


int main(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);
  
  using namespace precice;
  using namespace precice::constants;
  
  //std::mt19937::result_type seed = time(0);
  //auto real_rand = std::bind(std::uniform_real_distribution<double>(0,1), std::mt19937(seed));

  OptionMap options = getOptions(argc, argv);
  printOptions(options);
  std::string participant = options["participant"].as<std::string>();
  
  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

  precice::SolverInterface interface(participant, MPIrank, MPIsize);
  interface.configure(options["precice-config"].as<std::string>());
  int meshID = interface.getMeshID(options["mesh"].as<std::string>());
  int data1ID = interface.getDataID(options["data1"].as<std::string>(), meshID);
  int data2ID = interface.getDataID(options["data2"].as<std::string>(), meshID);

  Mesh mesh = getMyMesh(options, MPIrank, MPIsize);
  Data data1;
  Data data2;
 
  data1 = getData(mesh);
  data2 = getData(mesh);
  
  // printMesh(mesh, data);
  std::vector<int> vertexIDs;
  
  size_t localN = mesh.size();
  for (size_t i = 0; i < localN; i++) {
    vertexIDs.push_back(interface.setMeshVertex(meshID, static_cast<const double *>(mesh[i].data())));
  }
  
  interface.initialize();

  cout << "INITALIZED!!" << endl;
  
  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    if (participant == "A") {
      interface.writeBlockScalarData(data2ID, localN, vertexIDs.data(), data2.data());
    }else if (participant == "B"){
      interface.writeBlockScalarData(data1ID, localN, vertexIDs.data(), data1.data());
    }
    cout << "Wrote initial data = " << data2 << endl;
    interface.fulfilledAction(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();
  if (interface.isReadDataAvailable()) {
    if (participant == "A") {
      interface.readBlockScalarData(data1ID, localN, vertexIDs.data(), data1.data());
    }else if (participant == "B"){
      interface.readBlockScalarData(data2ID, localN, vertexIDs.data(), data2.data());
    }
  }

  while (interface.isCouplingOngoing()) {

    // When an implicit coupling scheme is used, checkpointing is required
    if (interface.isActionRequired(actionWriteIterationCheckpoint()))
      interface.fulfilledAction(actionWriteIterationCheckpoint());

    // evaluate model, i.e., get new data
    if (participant == "A") {
      data2 = getData(mesh);
    }else if (participant == "B"){
      data1 = getData(mesh);
    }
    
    if(MPIrank == 0)
      std::cout<<"new Data: \n"<<data1<<"\n\n"<<data2<<std::endl;

    // write data
    if (participant == "A") {
      interface.writeBlockScalarData(data2ID, localN, vertexIDs.data(), data2.data());
    }else if (participant == "B"){
      interface.writeBlockScalarData(data1ID, localN, vertexIDs.data(), data1.data());
    }
    interface.advance(0.1);

    // read data
    if (participant == "A") {
      interface.readBlockScalarData(data1ID, localN, vertexIDs.data(), data1.data());
    }else if (participant == "B"){
      interface.readBlockScalarData(data2ID, localN, vertexIDs.data(), data2.data());
    }

    if (interface.isActionRequired(actionReadIterationCheckpoint()))  // i.e. not yet converged
      interface.fulfilledAction(actionReadIterationCheckpoint());
    
  }
  interface.finalize();

  // printMesh(mesh, data);
  
  MPI_Finalize();

  return 0;
}
