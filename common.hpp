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
  po::options_description desc("ASET: Artificial solver emulation tool");
  desc.add_options()
    ("help,h", "produce help")
    ("precice-config,x", po::value<std::string>()->default_value("precice.xml"), "preCICE configuratio file")
    ("participant,p", po::value<std::string>()->required(), "Participant Name")
    ("mesh", po::value<std::string>()->required(), "Mesh Name")
    ("data1", po::value<std::string>()->default_value("Data1"), "Data1 Name")
    ("data2", po::value<std::string>()->default_value("Data2"), "Data2 Name")
    ("x", po::value<double>()->default_value(10), "X Mesh size")
    ("y", po::value<double>()->default_value(10), "Y Mesh size")
    ("nx", po::value<int>()->default_value(10), "Number of elements in y-direction")
    ("ny", po::value<int>()->default_value(10), "Number of elements in y-direction");
  
  // po::positional_options_description pd;
  // pd.add("participant", 1);
  // pd.add("mesh", 1);

  po::variables_map vm;        

  try {
    // po::store(po::command_line_parser(argc, argv).options(desc).positional(pd).run(), vm);
    po::store(parse_command_line(argc, argv, desc), vm);
    // po::store(po::parse_config_file("config", desc), vm);

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
  std::cout << "Mesh Name             : " << options["mesh"].as<std::string>() << std::endl;
  std::cout << "Data Name             : " << options["data1"].as<std::string>() << std::endl;
  std::cout << "Data Name             : " << options["data2"].as<std::string>() << std::endl;
  std::cout << "Mesh Size             : " << options["x"].as<double>() << ", " << options["y"].as<double>()<< std::endl;
  std::cout << "Mesh Elements         : " << options["nx"].as<int>() << ", " << options["ny"].as<int>()<< std::endl;
}

void printMesh(const Mesh &mesh, const Data &data)
{
  int MPIrank = 0, MPIsize = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
  MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);
  int rank = 0;
  while (rank < MPIsize) {
    if (MPIrank == rank) {
      std::cout << "==== MESH FOR RANK " << MPIrank << ", SIZE = " << mesh.size() << " ====" << std::endl;
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


