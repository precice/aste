#include "common.hpp"

using namespace std;

OptionMap getOptions(int argc, char *argv[])
{
  namespace po = boost::program_options;

  po::options_description desc("ASTE: Artificial solver emulation tool");
  desc.add_options()("help,h", "Print this help message")("aste-config", po::value<std::string>(), "ASTE Configuration file for replay mode")(
      "precice-config,c",
      po::value<std::string>()->default_value("precice-config.xml"),
      "preCICE configuratio file")(
      "participant,p",
      po::value<std::string>(),
      "Participant Name")(
      "data", po::value<std::string>(),
      "Name of Data Array to be Mapped")(
      "mesh", po::value<std::string>(),
      "Mesh prefix (i.e. mesh name without the format extension such as '.vtk' or '.vtu'). "
      "Example: solution.vtk has the prefix 'solution'. "
      "precice-aste-run will look for timeseries as well as distributed meshes (e.g. from preCICE exports) "
      "automatically and load them if required.")(
      "output", po::value<std::string>(),
      "Output file name.")(
      "vector", po::bool_switch(),
      "Distinguish between vector valued data and scalar data")("verbose,v", po::bool_switch(), "Enable verbose output"); // not explicitly used, handled by easylogging

  po::variables_map vm;

  try {
    po::store(parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      ASTE_INFO << desc << std::endl;
      std::exit(EXIT_SUCCESS);
    }

    // Needs to be called before we look for participants
    po::notify(vm);

    if (!vm.count("aste-config") && vm["participant"].as<string>() != "A" &&
        vm["participant"].as<string>() != "B")
      throw runtime_error("Invalid participant, must be either 'A' or 'B'");

    if (!(vm.count("participant") || vm.count("data") || vm.count("mesh") || vm.count("output") || vm.count("vector")) && vm.count("aste-config"))
      throw runtime_error("Replay mode can only be combined with logging options");

    if ((vm.count("aste-config") == 0) && not(vm.count("participant") && vm.count("data") && vm.count("mesh")))
      throw runtime_error("One of the following arguments is missing \"--participant\" \"--data\" \"--mesh\"");

  } catch (const std::exception &e) {
    ASTE_ERROR << "ERROR: " << e.what() << "\n";
    ASTE_ERROR << desc << std::endl;
    std::exit(EXIT_FAILURE);
  }
  return vm;
}
