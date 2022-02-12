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
      "precice-config,pc",
      po::value<std::string>()->default_value("precice-config.xml"),
      "preCICE configuration file")("aste-config,ac", po::value<std::string>()->required())("participant,p", po::value<std::string>()->required(), "Participant Name")("verbose,v", po::bool_switch(), "Enable verbose output"); // not explicitely used, handled by easylogging

  po::variables_map vm;

  try {
    po::store(parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      std::cout << desc << std::endl;
      std::exit(EXIT_SUCCESS);
    }

    // Needs to be called before we look for participants
    po::notify(vm);
  } catch (const std::exception &e) {
    LOG(ERROR) << "ERROR: " << e.what() << "\n";
    LOG(ERROR) << desc << std::endl;
    std::exit(EXIT_FAILURE);
  }
  return vm;
}
