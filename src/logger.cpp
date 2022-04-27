#include "logger.hpp"

namespace attrs   = boost::log::attributes;
namespace expr    = boost::log::expressions;
namespace logging = boost::log;

// Defines a global logger initialization routine
BOOST_LOG_GLOBAL_LOGGER_INIT(my_logger, src::severity_logger_mt<boost::log::trivial::severity_level>)
{
  src::severity_logger_mt<boost::log::trivial::severity_level> lg;
  logging::add_common_attributes();
  auto format = expr::stream << "---[ASTE] " << expr::message;
  logging::add_console_log(std::clog, keywords::format = format);
  logging::core::get()->set_filter(
      logging::trivial::severity >= logging::trivial::info);

  return lg;
}
