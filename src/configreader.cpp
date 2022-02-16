#include "configreader.hpp"
#include <iostream>

namespace aste {
void asteConfig::load(const std::string &asteConfigFile)
{
  YAML::Node config = YAML::LoadFile(asteConfigFile);

  preciceConfigFilename = config["precice-config"].as<std::string>();

  participantName = config["participant"].as<std::string>();

  const int numInterfaces = config["meshes"].size();

  for (auto i = 0; i < numInterfaces; i++) {
    asteInterface interface;
    interface.meshName       = config["meshes"][i]["mesh"].as<std::string>();
    interface.meshFilePrefix = config["meshes"][i]["meshfileprefix"].as<std::string>();

    const auto readScalarSize  = config["meshes"][i]["read-data"]["scalar"].size();
    const auto readVectorSize  = config["meshes"][i]["read-data"]["vector"].size();
    const auto writeScalarSize = config["meshes"][i]["write-data"]["scalar"].size();
    const auto writeVectorSize = config["meshes"][i]["write-data"]["vector"].size();

    for (auto k = 0; k < readScalarSize; k++) {
      const auto scalarName = config["meshes"][i]["read-data"]["scalar"][k].as<std::string>();
      interface.readScalarNames.push_back(scalarName);
    }
    for (auto k = 0; k < readVectorSize; k++) {
      const auto vectorName = config["meshes"][i]["read-data"]["vector"][k].as<std::string>();
      interface.readVectorNames.push_back(vectorName);
    }
    for (auto k = 0; k < writeScalarSize; k++) {
      const auto scalarName = config["meshes"][i]["write-data"]["scalar"][k].as<std::string>();
      interface.writeScalarNames.push_back(scalarName);
    }
    for (auto k = 0; k < writeVectorSize; k++) {
      const auto vectorName = config["meshes"][i]["write-data"]["vector"][k].as<std::string>();
      interface.writeVectorNames.push_back(vectorName);
    }
    asteInterfaces.push_back(interface);
  }

  return;
};

} // namespace aste
