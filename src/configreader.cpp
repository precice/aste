#include "configreader.hpp"

namespace aste {

void asteConfig::setDim(int dimension)
{
  _dimension = dimension;
  return;
};

int asteConfig::getDim()
{
  return _dimension;
}

} // namespace aste
