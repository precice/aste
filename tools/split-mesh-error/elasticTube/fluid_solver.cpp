#include <iostream>
#include <stdlib.h>
#include "precice/SolverInterface.hpp"

using std::cout;
using std::endl;

using namespace precice;
using namespace precice::constants;

int main(int argc, char **argv)
{
  cout << "Starting Fluid Solver..." << endl;

  if (argc != 5) {
    cout << endl;
    cout << "Usage: " << argv[0] << " configurationFileName N tau kappa" << endl;
    cout << endl;
    cout << "N:     Number of mesh elements." << endl;
    cout << "tau:   Dimensionless time step size." << endl;
    cout << "kappa: Dimensionless structural stiffness." << endl;
    return -1;
  }

  std::string configFileName(argv[1]);
  int         nx    = atoi(argv[2]);
  int         ny    = atoi(argv[3]);
  int         nz    = atoi(argv[4]);
  double      tau   = 0.01;
  double      kappa = 100;
  int         N     = nx * ny * nz;

  double lenX = 20 / nx;
  double lenY = 20 / ny;
  double lenZ = 6 / nz;

  std::cout << "N: " << N << " tau: " << tau << " kappa: " << kappa << std::endl;

  std::string solverName = "FLUID";

  std::string outputFilePrefix = "Postproc/out_fluid";

  cout << "Configure preCICE..." << endl;
  // Create preCICE with the solver's name, the rank, and the total number of processes.
  SolverInterface interface(solverName, configFileName, 0, 1);

  int     i;
  int     w       = 0;
  int     patchID = 0;
  double *velocity, *velocity_n, *pressure, *pressure_n, *crossSectionLength, *crossSectionLength_n, *grid;

  int dimensions = interface.getDimensions();

  velocity             = new double[N];
  velocity_n           = new double[N];
  pressure             = new double[N];
  pressure_n           = new double[N];
  crossSectionLength   = new double[N];
  crossSectionLength_n = new double[N];
  grid                 = new double[dimensions * N];

  // get IDs from preCICE
  int meshID               = interface.getMeshID("Fluid_Nodes");
  int crossSectionLengthID = interface.getDataID("CrossSectionLength", meshID);
  int pressureID           = interface.getDataID("Pressure", meshID);

  for (double k = 0; k < nz; k++) {
    for (double j = 0; j < ny; j++) {
      for (double i = 0; i < nx; i++) {
        grid[w * 3]     = i * lenX;
        grid[w * 3 + 1] = j * lenY;
        grid[w * 3 + 2] = k * lenZ;
        pressure[w]     = (0.1 - (k * lenZ) / 2) * ((i * lenX) + (j * lenY));
        //pressure[w] = 1;
        pressure_n[w]         = pressure[w];
        crossSectionLength[w] = (0.1 - (k * lenZ) / 2) * ((i * lenX) + (j * lenY));
        //crossSectionLength[w] = 1;
        crossSectionLength_n[w] = crossSectionLength[w];
        std::cout << "Grid points are: X = " << grid[w * 3] << ", Y = " << grid[w * 3 + 1] << ", Z = " << grid[w * 3 + 2] << std::endl;
        std::cout << "Pressure = " << pressure[w] << std::endl;
        //patchIDs[w] = 1;
        //dataIndices[w] = interface.setMeshVertex(meshID, vertices[w].data());
        w++;
      }
    }
  }

  int *vertexIDs;
  vertexIDs = new int[N];

  // init data values and mesh
  for (i = 0; i < N; i++) {
    velocity[i]   = 1.0 / (kappa * 1.0);
    velocity_n[i] = 1.0 / (kappa * 1.0);
    //crossSectionLength[i]   = 1.0;
    //crossSectionLength_n[i] = 0.0;
    //pressure[i]             = 0.0;
    //pressure_n[i]           = 0.0;

    //for (int dim = 0; dim < dimensions; dim++)
    //  grid[i * dimensions + dim] = i * (1 - dim);
  }

  double t  = 0.0; // time
  double dt = 1;   // solver timestep size

  // tell preCICE about your coupling interface mesh
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

  cout << "Initialize preCICE..." << endl;
  interface.initialize();

  // write initial data if required
  if (interface.isActionRequired(actionWriteInitialData())) {
    interface.writeBlockScalarData(pressureID, N, vertexIDs, pressure);
    interface.markActionFulfilled(actionWriteInitialData());
  }

  // initial data is sent or received if necessary
  interface.initializeData();

  // read data if available
  if (interface.isReadDataAvailable()) {
    interface.readBlockScalarData(crossSectionLengthID, N, vertexIDs, crossSectionLength);
  }

  int out_counter = 0;

  while (interface.isCouplingOngoing()) {
    // for an implicit coupling, you can store an iteration checkpoint here (from the first iteration of a timestep)
    // this is, however, not necessary for this scenario
    if (interface.isActionRequired(actionWriteIterationCheckpoint())) {
      interface.markActionFulfilled(actionWriteIterationCheckpoint());
    }

    for (int i = 0; i < N; i++) {
      std::cout << "patch ID = : " << interface.getMeshVertexPatch(meshID, i) << std::endl;
    }

    // Modify values of pressure
    if (out_counter > 1) {
      for (int i = 0; i < N; i++) {
        if (N > nx * ny) {
          pressure[i] = -1;
        }
        std::cout << "pressure: " << pressure[i] << std::endl;
      }
    } else {
      for (int i = 0; i < N; i++) {
        std::cout << "pressure: " << pressure[i] << std::endl;
      }
    }

    // write pressure data to precice
    interface.writeBlockScalarData(pressureID, N, vertexIDs, pressure);

    interface.advance(dt);

    // read crossSectionLength data from precice
    interface.readBlockScalarData(crossSectionLengthID, N, vertexIDs, crossSectionLength);
    for (int i = 0; i < N; i++) {
      std::cout << "crossSectionLength: " << crossSectionLength[i] << std::endl;
    }
    for (int i = 0; i < N; i++) {
      std::cout << "error: " << crossSectionLength[i] - crossSectionLength_n[i] << std::endl;
    }

    // set variables back to checkpoint
    //if (interface.isActionRequired(actionReadIterationCheckpoint())) {
    // i.e. not yet converged, you could restore a checkpoint here (not necessary for this scenario)
    //   interface.markActionFulfilled(actionReadIterationCheckpoint());
    // }
    //else{
    //t += dt;
    //for (i = 0; i < N; i++) {
    //velocity_n[i]           = velocity[i];
    //pressure_n[i]           = pressure[i];
    //crossSectionLength_n[i] = crossSectionLength[i];
    //}
    //write_vtk(t, out_counter, outputFilePrefix.c_str(), N, grid, velocity_n, pressure, crossSectionLength, crossSectionLength_n);
    out_counter++;
    //}
  }

  interface.finalize();

  delete[] velocity;
  delete[] velocity_n;
  delete[] pressure;
  delete[] pressure_n;
  delete[] crossSectionLength;
  delete[] crossSectionLength_n;
  delete[] vertexIDs;
  delete[] grid;

  return 0;
}
