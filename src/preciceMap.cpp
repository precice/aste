#include <mpi.h>
#include <string>
#include "thirdparty/easylogging++.h"
#include "modes.hpp"
#include "utilities.hpp"

INITIALIZE_EASYLOGGINGPP

int main(int argc, char *argv[])
{
  START_EASYLOGGINGPP(argc, argv);
  auto context = aste::initializeMPI(argc, argv);
  auto options = getOptions(argc, argv);

  if (options.count("aste-config")) {
    aste::runReplayMode(context, options["aste-config"].as<std::string>());
  } else {
    aste::runMapperMode(context, options);
  }
  MPI_Finalize();
  return EXIT_SUCCESS;
}
