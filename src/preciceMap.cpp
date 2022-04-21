#include <mpi.h>
#include <string>
#include "logger.hpp"
#include "modes.hpp"
#include "utilities.hpp"

int main(int argc, char *argv[])
{
  auto context = aste::initializeMPI(argc, argv);
  auto options = getOptions(argc, argv);

  if (options["verbose"].as<bool>()) {
    boost::log::core::get()->set_filter(logging::trivial::severity >= logging::trivial::debug);
  }

  if (options.count("aste-config")) {
    ASTE_INFO << "ASTE Running on re-play mode";
    aste::runReplayMode(context, options["aste-config"].as<std::string>());
  } else {
    ASTE_INFO << "ASTE Running on mapping test mode";
    aste::runMapperMode(context, options);
  }
  ASTE_INFO << "Finalizing ASTE";
  MPI_Finalize();
  return EXIT_SUCCESS;
}
