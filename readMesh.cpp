// #include "common.hpp"

#include <fstream>
#include <iostream>
#include <mpi.h>
#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>
#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"
#include "utils/EventTimings.hpp"


using std::string;
using std::endl;
using std::cout;
namespace fs = boost::filesystem;

int countLines(std::string file)
{
  std::ifstream inFile(file);
  return std::count(std::istreambuf_iterator<char>(inFile),
                    std::istreambuf_iterator<char>(), '\n');
}

boost::program_options::variables_map getOptions(int argc, char *argv[])
{
  namespace po = boost::program_options;
  using std::cout; using std::endl;
  po::options_description options("Reads a mesh with values, does one timestep.");
  po::options_description hidden("Hidden");
  po::options_description allArgs("All Args");
  po::positional_options_description positional;
  
  options.add_options()
    ("help,h", "Produce help")
    ("precice-config,c", po::value<string>()->default_value("precice.xml"), "preCICE configuration file.")
    ("output,o", po::value<std::string>()->default_value("output"), "Directory to write output files to.")
    ("vpr", po::value<int>()->default_value(-1), "Vertices per rank or -1 if it should be read from file.")
    ("autodist,a", po::bool_switch(), "Automatically distribute vertices among ranks.")
    ("runName", po::value<std::string>()->default_value(""), "Name of the run");

  hidden.add_options()
    ("meshFile", po::value<string>()->required())
    ("participant", po::value<string>()->required());

  positional.add("meshFile", 1);
  positional.add("participant", 1);

  allArgs.add(options).add(hidden);
    
  po::variables_map vm;        

  string usageHelp = string("Usage: ") + argv[0] + " [options] <meshInputFile> <participant A or B>";
  try {
    po::store(po::command_line_parser(argc, argv).options(allArgs).positional(positional).run(), vm);
          
    if (vm.count("help")) {
      cout << usageHelp << endl;
      cout << options << endl;
      std::exit(0);
    }
    po::notify(vm);
  }
  catch(po::error& e) {
    cout << "ERROR: " << e.what() << "\n\n";
    cout << usageHelp << endl;
    cout << options << endl;
    std::exit(-1);
  }
  return vm;
}

int main(int argc, char *argv[])
{
  MPI_Init(&argc, &argv);

  auto options = getOptions(argc, argv);

  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);


  string participant = options["participant"].as<string>();
    
  precice::SolverInterface interface(participant, MPIrank, MPIsize);
  // precice::utils::Event _eTotal("Total");
  interface.configure(options["precice-config"].as<string>());
  precice::utils::EventRegistry::instance().runName = options["runName"].as<std::string>();
  
  int meshID = interface.getMeshID( (participant == "A") ? "MeshA" : "MeshB" ); // participant = A => MeshID = MeshA
  int dataID = interface.getDataID("Data", meshID);
  std::vector<int> vertexIDs;
  std::vector<double> data;
  std::vector<std::array<double, 3>> positions;
  double x, y, z, val;
  int rank = 0, i = 0;
  std::string meshFile = options["meshFile"].as<string>();
  
  int vpr = 0; // Vertices per rank
  
  if (options["autodist"].as<bool>())
    vpr = countLines(meshFile) / MPIsize;
  else
    vpr = options["vpr"].as<int>();

  std::ifstream infile(meshFile);
    
  while (infile >> x >> y >> z >> val >> rank ) {
    if ( ((vpr == -1) and (rank == MPIrank)) or
         ((vpr > 0) and (i >= MPIrank*vpr) and (i < (MPIrank+1)*vpr)) ) {
      std::array<double, 3> vertexPos = {x, y, z};
      vertexIDs.push_back(interface.setMeshVertex(meshID, vertexPos.data()));
      positions.push_back(vertexPos);
      data.push_back(val);
    }
    i++;
  }
  infile.close();

  std::cout << "(" << rank << ") Read in " << vertexIDs.size() << " vertices " << " from " << meshFile << std::endl;
  
  if (participant == "B")
    data = std::vector<double>(vertexIDs.size(), 0);
  
  interface.initialize();
  
  if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
    std::cout << "Write initial data for participant " << participant << std::endl;
    interface.writeBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
    interface.fulfilledAction(precice::constants::actionWriteInitialData());
  }
  interface.initializeData();

  while (interface.isCouplingOngoing()) {
    if (participant == "A" and not data.empty()) {
      // std:: cout << "Rank = " << MPIrank << " A writes data." << std::endl;
      interface.writeBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
    }
    interface.advance(1);
    
    if (participant == "B") {
      // std::cout << "Rank = " << MPIrank << " B reads data." << std::endl;
      interface.readBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
    }
  }

  // Write out results in same format as data was read
  if (participant == "B") {
    fs::path outfile(options["output"].as<string>());
    fs::create_directory(outfile);
    outfile = outfile / fs::path(string("rank_") + std::to_string(MPIrank));
    std::ofstream ostream(outfile.string(), std::ios::trunc);
    ostream.precision(9);
    for (size_t i = 0; i < data.size(); i++) {
      ostream << positions[i][0] << " " << positions[i][1] << " " << positions[i][2] << " " << data[i] << " " << MPIrank << std::endl;
    }
    ostream.close();
  }

  interface.finalize();
    
  MPI_Finalize();
  
  return 0;
}
