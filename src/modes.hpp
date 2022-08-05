#pragma once

#include <cassert>
#include <iostream>
#include <string>

#include "common.hpp"
#include "configreader.hpp"
#include "logger.hpp"
#include "mesh.hpp"
#include "utilities.hpp"

#include "precice/SolverInterface.hpp"

namespace aste {
/**
 * @brief The function runs ASTE in replay mode where aste simulates a participant in preCICE
 *
 * @param context
 * @param asteConfigName ASTE configuration filename
 */
void runReplayMode(const aste::ExecutionContext &context, const std::string &asteConfigName);

/**
 * @brief The function runs ASTE in mapper mode in which a given data is mapped from participant A to B.
 *
 * @param context
 * @param options
 */
void runMapperMode(const aste::ExecutionContext &context, const OptionMap &options);
} // namespace aste
