#include <boost/log/attributes/constant.hpp>
#include <mpi.h>
#include <string>
#include "logger.hpp"
#include "modes.hpp"
#include "utilities.hpp"

int main(int argc, char *argv[])
{
  auto context = aste::initializeMPI(argc, argv);
  auto options = getOptions(argc, argv);

  addLogSink(
      options["verbose"].as<bool>() ? LogLevel::Verbose : LogLevel::Quiet,
      options["all"].as<bool>() ? LogRankFilter::All : LogRankFilter::OnlyPrimary);

  if (options.count("aste-config")) {
    aste::runReplayMode(context, options["aste-config"].as<std::string>());
  } else {
    aste::runMapperMode(context, options);
  }
  ASTE_INFO << "Finalizing ASTE";
  MPI_Finalize();
  return EXIT_SUCCESS;
}
