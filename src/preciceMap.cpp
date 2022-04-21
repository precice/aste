#include <mpi.h>
#include <string>
#include "logger.hpp"
#include "modes.hpp"
#include "utilities.hpp"

int main(int argc, char *argv[])
{
  INIT_LOGGING(info);
  auto context = aste::initializeMPI(argc, argv);
  auto options = getOptions(argc, argv);

  if (options["verbose"].as<bool>()) {
    CHANGE_LOG_SEV_LEVEL(debug);
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
