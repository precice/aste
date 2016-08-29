#include <iostream>
#include <mpi.h>
#include <boost/program_options.hpp>

#include "utils/prettyprint.hpp"

using namespace std;

/// A single vertex, holding it's coordinates
using Vertex = std::vector<double>;

/// The serialized mesh
using Mesh = std::vector<Vertex>;

/// The data, living at each mesh node
using Data = std::vector<double>;

using OptionMap = boost::program_options::variables_map;

OptionMap getOptions(int argc, char *argv[])
{
  namespace po = boost::program_options;
  using std::cout; using std::endl;
  po::options_description desc("ASTE: Artificial solver emulation tool");
  desc.add_options()
    ("help,h", "produce help")
    ("precice-config,c", po::value<std::string>()->default_value("precice.xml"), "preCICE configuratio file")
    ("participant,p", po::value<std::string>()->required(), "Participant Name")
    ("x", po::value<double>()->default_value(10), "X Mesh size")
    ("y", po::value<double>()->default_value(10), "Y Mesh size")
    ("nx", po::value<int>()->default_value(10), "Number of elements in y-direction")
    ("ny", po::value<int>()->default_value(10), "Number of elements in y-direction")
    ("deadrank", po::value<int>()->default_value(-1), "A rank that is not used")
    ("printMesh", po::bool_switch(), "Print the full mesh");
  
  po::variables_map vm;        

  try {
    po::store(parse_command_line(argc, argv, desc), vm);
    
    if (vm.count("help")) {
      std::cout << desc << std::endl;
      std::exit(-1);
    }
    po::notify(vm);
  }
  catch(po::error& e) {
    std::cout << "ERROR: " << e.what() << "\n\n";
    std::cout << desc << std::endl;
    std::exit(-1);
  }
  return vm;  
}

void printOptions(const OptionMap &options)
{
  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

  if (MPIrank != 0)
    return;

  std::cout << "Running as participant: " << options["participant"].as<std::string>() << std::endl;
  std::cout << "Running as MPI rank   : " << MPIrank << " of " << MPIsize << std::endl;
  std::cout << "preCICE configuration : " << options["precice-config"].as<std::string>() << std::endl;
  std::cout << "Mesh Size             : " << options["x"].as<double>() << ", " << options["y"].as<double>()<< std::endl;
  std::cout << "Mesh Elements         : " << options["nx"].as<int>() << ", " << options["ny"].as<int>()<< std::endl;
  std::cout << "Dead Rank             : " << options["deadrank"].as<int>() << std::endl;
}

void printMesh(const Mesh &mesh, const Data &data, bool verbose)
{
  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);
  int rank = 0;
  while (rank < MPIsize) {
    if (MPIrank == rank) {
      std::cout << "==== MESH FOR RANK " << MPIrank << ", SIZE = " << mesh.size() << " ====" << std::endl;
      if (verbose)
        for (size_t i = 0; i < mesh.size(); i++)
          std::cout << "[" << mesh[i] << "]" << " = " << data[i] << std::endl;
      std::cout << std::flush;
    }
    rank++;
  }
   
  MPI_Barrier(MPI_COMM_WORLD);
}



// Partitions range in equal chunks
template<typename T>
std::vector<T> partition(T& range, int num)
{
  int partSize = range.size() / num;
  std::vector<T> partitions;
  for (int i = 0; i < num; i++) {
    if (i==num-1)
      partitions.emplace_back(range.begin()+(i*partSize), range.end());
    else
      partitions.emplace_back(range.begin()+(i*partSize), range.begin()+((i+1)*partSize));
    
  }
  return partitions;
    
}


