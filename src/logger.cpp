#include "logger.hpp"
#include <boost/log/attributes/constant.hpp>

namespace attrs   = boost::log::attributes;
namespace expr    = boost::log::expressions;
namespace logging = boost::log;

// Defines a global logger initialization routine
BOOST_LOG_GLOBAL_LOGGER_INIT(my_logger, src::severity_logger_mt<logging::trivial::severity_level>)
{
  src::severity_logger_mt<logging::trivial::severity_level> lg;
  lg.add_attribute("ASTE", attrs::constant<bool>(true));
  logging::add_common_attributes();
  return lg;
}

void addLogIdentity(const std::string &participant, int rank)
{
  my_logger::get().add_attribute("Participant", attrs::constant<std::string>(participant));
  my_logger::get().add_attribute("Rank", attrs::constant<int>(rank));
}

void addLogSink(bool verbose)
{
  std::string filter = "( %Severity% >= ";
  filter.append(verbose ? "debug" : "info");
  filter.append(" ) and %ASTE%");
  std::cerr << filter;

  std::string formatter = "---[ASTE:%Participant%:%Rank%] %Message%";
  ;

  logging::add_console_log(
      std::clog,
      keywords::format = logging::parse_formatter(formatter),
      keywords::filter = logging::parse_filter(filter));
}
