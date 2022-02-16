#include <string>
#include <vector>
#include "mesh.hpp"
#include "precice/SolverInterface.hpp"
#include "yaml-cpp/yaml.h"

namespace aste {

struct asteInterface {
  std::string              meshName;
  std::string              meshFilePrefix;
  std::vector<std::string> writeVectorNames;
  std::vector<std::string> readVectorNames;
  std::vector<std::string> writeScalarNames;
  std::vector<std::string> readScalarNames;
  std::vector<MeshName>    meshes;
  int                      meshID;
  Mesh                     mesh;
};

class asteConfig {
public:
  void                       load(const std::string &asteConfigFile);
  std::string                preciceConfigFilename;
  std::vector<asteInterface> asteInterfaces;
  std::string                participantName;
};

} // namespace aste
