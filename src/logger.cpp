#include "logger.hpp"
#include <boost/log/attributes/constant.hpp>
#include <boost/log/detail/trivial_keyword.hpp>
#include <boost/log/expressions/filter.hpp>
#include <boost/log/expressions/formatters/if.hpp>
#include <boost/log/expressions/formatters/stream.hpp>
#include <boost/log/expressions/message.hpp>
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

void addLogSink(LogLevel ll, LogRankFilter lrf)
{
  int loglevel = (ll == LogLevel::Verbose) ? logging::trivial::debug : logging::trivial::info;

  auto filter = [&]() -> logging::filter {
    if (lrf == LogRankFilter::OnlyPrimary) {
      return logging::trivial::severity >= loglevel & (expr::attr<int>("Rank").or_default(0) == 0);
    } else {
      return logging::trivial::severity >= loglevel;
    }
  }();

  // Either "ASTE" or "preCICE"
  auto origin = expr::if_(expr::has_attr<bool>("ASTE"))[expr::stream << "ASTE"].else_[expr::stream << "preCICE"];

  // For preCICE logs "(Module in Function)" if verbose
  auto location = expr::if_((ll == LogLevel::Verbose) && !expr::has_attr<bool>("ASTE"))
      [expr::stream << "(" << expr::attr<std::string>("Module") << " in " << expr::attr<std::string>("Function") << ") "];

  // Format the severity
  auto blankSeverity =
      expr::if_(logging::trivial::error == logging::trivial::severity)
          [expr::stream << "ERROR"]
              .else_[expr::stream << expr::if_(logging::trivial::warning == logging::trivial::severity)
                                         [expr::stream << "WARNING"]
                                             .else_[expr::stream << expr::if_(logging::trivial::info == logging::trivial::severity)
                                                                        [expr::stream << "INFO"]
                                                                            .else_[expr::stream << expr::if_(logging::trivial::debug == logging::trivial::severity)
                                                                                                       [expr::stream << "DEBUG"]
                                                                                                           .else_[expr::stream << logging::trivial::severity]]]];

  auto formatter = expr::stream
                   << "---["
                   << origin
                   << ':' << expr::attr<std::string>("Participant")
                   << ':' << expr::attr<int>("Rank")
                   << "] "
                   << location
                   << blankSeverity
                   << " : " << expr::smessage;

  logging::add_console_log(
      std::clog,
      keywords::format = formatter,
      keywords::filter = filter);
}
