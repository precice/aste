#include "configreader.hpp"
#include <fstream>
#include <iostream>

namespace aste {
void asteConfig::load(const std::string &asteConfigFile)
{

  std::ifstream ifs(asteConfigFile);
  json          config = json::parse(ifs);

  preciceConfigFilename = config["precice-config"];

  participantName = config["participant"];

  starttime = config["starttime"].get<int>();
  if (starttime < 1) {
    throw std::runtime_error("Start time cannot be smaller than 1, check your ASTE configuration file.");
  }

  const int numInterfaces = config["meshes"].size();

  for (auto i = 0; i < numInterfaces; i++) {
    asteInterface interface;
    interface.meshName       = config["meshes"][i]["mesh"];
    interface.meshFilePrefix = config["meshes"][i]["meshfileprefix"];

    const auto readScalarSize  = config["meshes"][i]["read-data"]["scalar"].size();
    const auto readVectorSize  = config["meshes"][i]["read-data"]["vector"].size();
    const auto writeScalarSize = config["meshes"][i]["write-data"]["scalar"].size();
    const auto writeVectorSize = config["meshes"][i]["write-data"]["vector"].size();

    for (auto k = 0; k < readScalarSize; k++) {
      const auto scalarName = config["meshes"][i]["read-data"]["scalar"][k];
      interface.readScalarNames.push_back(scalarName);
    }
    for (auto k = 0; k < readVectorSize; k++) {
      const auto vectorName = config["meshes"][i]["read-data"]["vector"][k];
      interface.readVectorNames.push_back(vectorName);
    }
    for (auto k = 0; k < writeScalarSize; k++) {
      const auto scalarName = config["meshes"][i]["write-data"]["scalar"][k];
      interface.writeScalarNames.push_back(scalarName);
    }
    for (auto k = 0; k < writeVectorSize; k++) {
      const auto vectorName = config["meshes"][i]["write-data"]["vector"][k];
      interface.writeVectorNames.push_back(vectorName);
    }
    asteInterfaces.push_back(interface);
  }

  return;
};

} // namespace aste
