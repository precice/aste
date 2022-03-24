#pragma once

#include <cassert>
#include <string>
#include "common.hpp"
#include "configreader.hpp"
#include "easylogging++.h"
#include "mesh.hpp"
#include "precice/SolverInterface.hpp"

namespace aste {
void runReplayMode(const aste::ExecutionContext &context, const std::string &asteConfigName);
void runMapperMode(const aste::ExecutionContext &context, const OptionMap &options);
} // namespace aste