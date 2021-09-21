#include "common.hpp"
#include <boost/program_options.hpp>
#include <iostream>
#include <mpi.h>
#include "easylogging++.h"

using namespace std;

OptionMap getOptions(int argc, char *argv[])
{
  namespace po = boost::program_options;
  using std::cout;
  using std::endl;
  po::options_description desc("ASTE: Artificial solver emulation tool");
  desc.add_options()("help,h", "produce help")(
      "precice-config,c",
      po::value<std::string>()->default_value("precice.xml"),
      "preCICE configuratio file")("participant,p",
                                   po::value<std::string>()->required(),
                                   "Participant Name")(
      "runName", po::value<std::string>()->default_value(""),
      "Name of the run")("data", po::value<std::string>()->required(),
                         "Name of Data Array to be Mapped")(
      "mesh", po::value<string>()->required(),
      "Mesh directory. For each timestep i there will be .dti (e.g. .dt4) "
      "appended to the directory name")(
      "output", po::value<string>()->default_value("output"),
      "Output file name.")(
      "vector", po::bool_switch(),
      "Is used data a vector")(
      "verbose,v", po::bool_switch(),
      "Enable verbose output") // not explicitely used, handled by easylogging
      ;

  po::variables_map vm;

  try {
    po::store(parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      std::cout << desc << std::endl;
      std::exit(-1);
    }
    if (vm["participant"].as<string>() != "A" &&
        vm["participant"].as<string>() != "B")
      throw runtime_error("Invalid participant, must be either 'A' or 'B'");
    po::notify(vm);
  } catch (const std::exception &e) {
    LOG(ERROR) << "ERROR: " << e.what() << "\n";
    LOG(ERROR) << desc << std::endl;
    std::exit(-1);
  }
  return vm;
}
