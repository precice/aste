#include <string>
#include <vector>
#include "mesh.hpp"
#include "precice/SolverInterface.hpp"
#include "yaml-cpp/yaml.h"

namespace aste {

enum dataType { VECTOR,
                SCALAR };

struct asteInterface {
  std::string              meshName;
  std::string              meshFilePrefix;
  std::vector<std::string> writeVectorNames;
  std::vector<std::string> readVectorNames;
  std::vector<std::string> writeScalarNames;
  std::vector<std::string> readSCalarNames;
  std::vector<MeshName>    meshes;
  int                      meshID;
};

struct asteParticipant {
  std::string                participantName;
  std::vector<asteInterface> asteInterfaces;
  precice::SolverInterface   preciceInferface;
};

class asteConfig {
public:
  void                         load(std::string asteConfigFile);
  asteParticipant              getParticipant(int id);
  std::vector<asteParticipant> getParticipants();
  void                         setDim(int dimension);
  int                          getDim();

private:
  std::vector<asteParticipant> _participants;
  int                          _dimension;
};

} // namespace aste
