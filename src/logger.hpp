#pragma once

/*
 *          Copyright Andrey Semashev 2007 - 2015.
 * Distributed under the Boost Software License, Version 1.0.
 *    (See accompanying file LICENSE_1_0.txt or copy at
 *          http://www.boost.org/LICENSE_1_0.txt)
 */

#include <boost/log/common.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sources/logger.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/utility/setup/console.hpp>
#include <iostream>

namespace logging  = boost::log;
namespace sinks    = boost::log::sinks;
namespace attrs    = boost::log::attributes;
namespace src      = boost::log::sources;
namespace expr     = boost::log::expressions;
namespace keywords = boost::log::keywords;

using boost::shared_ptr;

// Here we define our application severity levels.
enum severity_level {
  debug,
  info,
  warning,
  error,
  critical
};

// The formatting logic for the severity level
template <typename CharT, typename TraitsT>
inline std::basic_ostream<CharT, TraitsT> &operator<<(
    std::basic_ostream<CharT, TraitsT> &strm, severity_level lvl)
{
  static const char *const str[] =
      {
          "DEBUG",
          "INFO",
          "WARNING",
          "ERROR",
          "CRITICAL"};
  if (static_cast<std::size_t>(lvl) < (sizeof(str) / sizeof(*str)))
    strm << str[lvl];
  else
    strm << static_cast<int>(lvl);
  return strm;
}

BOOST_LOG_ATTRIBUTE_KEYWORD(severity, "Severity", severity_level)

BOOST_LOG_INLINE_GLOBAL_LOGGER_DEFAULT(aste_logger, src::severity_logger<severity_level>)

#define INIT_LOGGING(LEVEL)                                         \
  ({                                                                \
    auto format = expr::stream << "---[ASTE] " << expr::message;    \
    logging::add_console_log(std::clog, keywords::format = format); \
    logging::core::get()->set_filter(severity >= LEVEL);            \
    BOOST_LOG_FUNCTION();                                           \
  })

#define CHANGE_LOG_SEV_LEVEL(LEVEL) ({                 \
  logging::core::get()->set_filter(severity >= LEVEL); \
})

#define ASTE_DEBUG BOOST_LOG_SEV(aste_logger::get(), debug)
#define ASTE_INFO BOOST_LOG_SEV(aste_logger::get(), info)
#define ASTE_WARNING BOOST_LOG_SEV(aste_logger::get(), warning)
#define ASTE_ERROR BOOST_LOG_SEV(aste_logger::get(), error)
#define ASTE_CRITICAL BOOST_LOG_SEV(aste_logger::get(), critical)