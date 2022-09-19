#include "logger.hpp"
#include <boost/log/attributes/constant.hpp>
#include <boost/log/expressions/formatters/if.hpp>
#include <boost/log/expressions/predicates/has_attr.hpp>
#include <boost/log/trivial.hpp>

namespace attrs   = boost::log::attributes;
namespace expr    = boost::log::expressions;
namespace logging = boost::log;

// Defines a global logger initialization routine
BOOST_LOG_GLOBAL_LOGGER_INIT(my_logger, logger_t)
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
  int loglevel = verbose ? logging::trivial::debug : logging::trivial::info;

  // Either "ASTE" or "preCICE"
  auto origin = expr::if_(expr::has_attr<bool>("ASTE"))[expr::stream << "ASTE"].else_[expr::stream << "preCICE"];

  // For preCICE logs "(Module in Function)" if verbose
  auto location = expr::if_(verbose && !expr::has_attr<bool>("ASTE"))
      [expr::stream << "(" << expr::attr<std::string>("Module") << " in " << expr::attr<std::string>("Function") << ") "];

  auto formatter = expr::stream
                   << "---["
                   << origin
                   << ':' << expr::attr<std::string>("Participant")
                   << ':' << expr::attr<int>("Rank")
                   << "] "
                   << location
                   << expr::smessage;

  logging::add_console_log(
      std::clog,
      keywords::format = formatter,
      keywords::filter = logging::trivial::severity >= loglevel);
}
