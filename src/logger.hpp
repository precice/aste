#pragma once

/*
 *          Copyright Andrey Semashev 2007 - 2015.
 * Distributed under the Boost Software License, Version 1.0.
 *    (See accompanying file LICENSE_1_0.txt or copy at
 *          http://www.boost.org/LICENSE_1_0.txt)
 */

#define BOOST_ALL_DYN_LINK

#include <boost/log/common.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sources/global_logger_storage.hpp>
#include <boost/log/sources/logger.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/utility/setup.hpp>
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

//Narrow-char thread-safe logger.
typedef boost::log::sources::severity_logger_mt<boost::log::trivial::severity_level> logger_t;

//declares a global logger with a custom initialization
BOOST_LOG_GLOBAL_LOGGER(my_logger, logger_t)

#define ASTE_DEBUG BOOST_LOG_SEV(my_logger::get(), boost::log::trivial::severity_level::debug)
#define ASTE_INFO BOOST_LOG_SEV(my_logger::get(), boost::log::trivial::severity_level::info)
#define ASTE_WARNING BOOST_LOG_SEV(my_loggermy_logger::get(), boost::log::trivial::severity_level::warning)
#define ASTE_ERROR BOOST_LOG_SEV(my_logger::get(), boost::log::trivial::severity_level::error)