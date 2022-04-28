#include <iostream>
#include <stdlib.h>
#include "precice/SolverInterface.hpp"
//#include "mpi.h"

using std::cout;
using std::endl;

void printData(const std::vector<double> &data)
{
  cout << "Received data = " << data[0];
  for (size_t i = 1; i < data.size(); i++) {
    cout << ", " << data[i];
  }
  cout << endl;
}

int main(int argc, char **argv)
{
  cout << "Starting Structure Solver..." << endl;
  using namespace precice;
  using namespace precice::constants;

  if (argc != 5) {
    cout << endl;
    cout << "Usage: " << argv[0] << " configurationFileName N" << endl;
    cout << endl;
    cout << "N:     Number of mesh elements, needs to be equal for fluid and structure solver." << endl;
    return -1;
  }

  std::string configFileName(argv[1]);
  int         nx      = atoi(argv[2]);
  int         ny      = atoi(argv[3]);
  int         nz      = atoi(argv[4]);
  int         N       = nx * ny * nz;
  int         w       = 0;
  int         patchID = 0;

  double lenX = 20 / nx;
  double lenY = 20 / ny;
  double lenZ = 2 / nz;

  std::cout << "N: " << N << std::endl;

  std::string solverName = "STRUCTURE";

  SolverInterface interface(solverName, configFileName, 0, 1);
  cout << "preCICE configured..." << endl;

  //init data
  double *crossSectionLength, *crossSectionLength_n, *pressure, *pressure_n;
  int     dimensions   = interface.getDimensions();
  crossSectionLength   = new double[N]; // Second dimension (only one cell deep) stored right after the first dimension: see SolverInterfaceImpl::setMeshVertices
  crossSectionLength_n = new double[N];
  pressure             = new double[N];
  pressure_n           = new double[N];
  double *grid;
  grid = new double[dimensions * N];

  for (double k = 0; k < nz; k++) {
    for (double j = 0; j < ny; j++) {
      for (double i = 0; i < nx; i++) {
        grid[w * 3]     = i * lenX;
        grid[w * 3 + 1] = j * lenY;
        grid[w * 3 + 2] = k * lenZ;
        std::cout << "Grid points are: X = " << grid[w * 3] << ", Y = " << grid[w * 3 + 1] << ", Z = " << grid[w * 3 + 2] << std::endl;
        //pressure[w] = (0.1 - (k*lenZ)/2)*((i*lenX)+(j*lenY));
        pressure[w]           = 1;
        pressure_n[w]         = pressure[w];
        crossSectionLength[w] = (0.1 - (k * lenZ) / 2) * ((i * lenX) + (j * lenY));
        //crossSectionLength[w] = 1;
        crossSectionLength_n[w] = crossSectionLength[w];
        //dataIndices[w] = interface.setMeshVertex(meshID, vertices[w].data());
        w++;
      }
    }
  }

  double dt = 1;     // solver timestep size
  double precice_dt; // maximum precice timestep size

  //precice stuff
  int  meshID               = interface.getMeshID("Structure_Nodes");
  int  crossSectionLengthID = interface.getDataID("CrossSectionLength", meshID);
  int  pressureID           = interface.getDataID("Pressure", meshID);
  int *vertexIDs;
  vertexIDs = new int[N];

  int tstep_counter = 0; // number of time steps (only coupling iteration time steps)
  int t             = 0; // number of time steps (including subcycling time steps)
  int tsub          = 0; // number of current subcycling time steps
  int n_subcycles   = 0; // number of subcycles
  //int t_steps_total = 0; // number of total timesteps, i.e., t_steps*n_subcycles

  interface.setMeshVertices(meshID, N, grid, vertexIDs);

  w = 0;
  for (double k = 0; k < nz; k++) {
    for (double j = 0; j < ny; j++) {
      for (double i = 0; i < nx; i++) {
        patchID = 0;
        if (k > 0) {
          patchID = 1;
          cout << "PatchID = 1" << endl;
        } else {
          cout << "PatchID = 0" << endl;
        }
        interface.setMeshVertexPatch(meshID, w, patchID);
        w++;
      }
    }
  }

  cout << "Structure: init precice..." << endl;
  precice_dt = interface.initialize();

  n_subcycles = (int) (precice_dt / dt);
  //t_steps_total = 100*n_subcycles;

  if (interface.isActionRequired(actionWriteInitialData())) {
    interface.writeBlockScalarData(crossSectionLengthID, N, vertexIDs, crossSectionLength);
    //interface.initializeData();
    interface.markActionFulfilled(actionWriteInitialData());
  }

  interface.initializeData();

  if (interface.isReadDataAvailable()) {
    interface.readBlockScalarData(pressureID, N, vertexIDs, pressure);
  }

  while (interface.isCouplingOngoing()) {
    // When an implicit coupling scheme is used, checkpointing is required
    if (interface.isActionRequired(actionWriteIterationCheckpoint())) {

      if (tstep_counter > 0) {
        cout << "Advancing in time, finished timestep: " << tstep_counter << endl;
        t += n_subcycles;
        tsub = 0;
      }
      tstep_counter++;

      // write checkpoint, save state variables (not needed here, stationary solver)
      interface.markActionFulfilled(actionWriteIterationCheckpoint());
    }

    // choose smalles time step (sub-cycling if dt is smaller than precice_dt)
    dt = std::min(precice_dt, dt);

    // advance in time for subcycling
    tsub++;

    /*for (double k = 0; k < nz; k++){
      for (double j = 0; j < ny; j++){
        for (double i = 0; i < nx; i++){
          crossSectionLength[i] = (0.1 - (lenZ)/2)*((lenX)+(lenY));
	  std::cout << "crossSectionLength: " << crossSectionLength[i] << std::endl;
	}
      }
    }
*/

    // send crossSectionLength data to precice
    for (int i = 0; i < N; i++) {
      std::cout << "crossSectionLength: " << crossSectionLength[i] << std::endl;
    }
    interface.writeBlockScalarData(crossSectionLengthID, N, vertexIDs, crossSectionLength);

    // advance
    precice_dt = interface.advance(dt);

    // receive pressure data from precice
    interface.readBlockScalarData(pressureID, N, vertexIDs, pressure);
    for (int i = 0; i < N; i++) {
      std::cout << "pressure: " << pressure[i] << std::endl;
    }
    for (int i = 0; i < N; i++) {
      std::cout << "error: " << pressure[i] - pressure_n[i] << std::endl;
    }

    if (interface.isActionRequired(actionReadIterationCheckpoint())) {
      cout << "Iterate" << endl;
      tsub = 0;

      interface.markActionFulfilled(actionReadIterationCheckpoint());
    }
  }

  interface.finalize();

  delete[] crossSectionLength;
  delete[] pressure;
  delete[] grid;
  delete[] vertexIDs;

  cout << "Exiting StructureSolver" << endl;

  return 0;
}
