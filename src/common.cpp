#include "common.hpp"
#include <boost/program_options.hpp>
#include <iostream>
#include <mpi.h>
#include "easylogging++.h"

using namespace std;

OptionMap getOptions(int argc, char *argv[])
{
  namespace po = boost::program_options;

  po::options_description desc("ASTE: Artificial solver emulation tool");
  desc.add_options()("help,h", "Print this help message")(
      "precice-config,c",
      po::value<std::string>()->default_value("precice-config.xml"),
      "preCICE configuratio file")(
      "participant,p",
      po::value<std::string>()->required(),
      "Participant Name")(
      "data", po::value<std::string>()->required(),
      "Name of Data Array to be Mapped")(
      "mesh", po::value<string>()->required(),
      "Mesh prefix (i.e. mesh name without the format extension such as '.vtk' or '.vtu'). "
      "Example: solution.vtk has the prefix 'solution'. "
      "preciceMap will look for timeseries as well as distributed meshes (e.g. from preCICE exports) "
      "automatically and load them if required.")(
      "output", po::value<string>()->default_value("output"),
      "Output file name.")(
      "vector", po::bool_switch(),
      "Distinguish between vector valued data and scalar data")(
      "verbose,v", po::bool_switch(),
      "Enable verbose output")(
      "gradient", po::bool_switch(), "Input data has gradient data"
      ); // not explicitely used, handled by easylogging

  po::variables_map vm;

  try {
    po::store(parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      std::cout << desc << std::endl;
      std::exit(EXIT_SUCCESS);
    }

    // Needs to be called before we look for participants
    po::notify(vm);

    if (vm["participant"].as<string>() != "A" &&
        vm["participant"].as<string>() != "B")
      throw runtime_error("Invalid participant, must be either 'A' or 'B'");
  } catch (const std::exception &e) {
    LOG(ERROR) << "ERROR: " << e.what() << "\n";
    LOG(ERROR) << desc << std::endl;
    std::exit(EXIT_FAILURE);
  }
  return vm;
}
