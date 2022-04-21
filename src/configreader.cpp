#include "configreader.hpp"
#include <fstream>
#include <iostream>
#include <mpi.h>
namespace aste {
void asteConfig::load(const std::string &asteConfigFile)
{

  std::ifstream ifs(asteConfigFile);
  json          config = json::parse(ifs);

  try {
    preciceConfigFilename = config["precice-config"].get<std::string>();
  } catch (nlohmann::detail::parse_error) {
    std::cerr << "Error while parsing ASTE configuration file \"precice-config\" is missing\n";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  } catch (nlohmann::detail::type_error) {
    std::cerr << "Error while parsing ASTE configuration file \"precice-config\" is missing\n";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  try {
    participantName = config["participant"].get<std::string>();
  } catch (nlohmann::detail::parse_error) {
    std::cerr << "Error while parsing ASTE configuration file \"participant\" is missing\n";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  } catch (nlohmann::detail::type_error) {
    std::cerr << "Error while parsing ASTE configuration file \"participant\" is missing\n";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  try {
    startdt = config["startdt"].get<int>();
  } catch (nlohmann::detail::type_error) {
    try {
      startdt = std::stoi(config["startdt"].get<std::string>());
    } catch (nlohmann::detail::type_error) {
      std::cerr << "Error while parsing ASTE configuration file \"startdt\" is missing or has a wrong type, it must be an integer or integer convertable string.\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    } catch (std::invalid_argument) {
      std::cerr << "Error while parsing startdt from ASTE configuration file it must be an integer or integer convertable string.\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
  }

  if (startdt < 1) {
    throw std::runtime_error("Start dt cannot be smaller than 1, please check your ASTE configuration file.");
  }

  const int numInterfaces = config["meshes"].size();

  if (numInterfaces == 0) {
    std::cerr << "ASTE configuration should contain at least 1 mesh. Please check your ASTE configuration file.\n";
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  for (auto i = 0; i < numInterfaces; i++) {
    asteInterface interface;
    try {
      interface.meshName = config["meshes"][i]["mesh"].get<std::string>();
    } catch (nlohmann::detail::parse_error) {
      std::cerr << "Error while parsing ASTE configuration file \"mesh\" is missing\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    } catch (nlohmann::detail::type_error) {
      std::cerr << "Error while parsing ASTE configuration file \"mesh\" is missing or not a string\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    try {
      interface.meshFilePrefix = config["meshes"][i]["meshfileprefix"];
    } catch (nlohmann::detail::parse_error) {
      std::cerr << "Error while parsing ASTE configuration file \"meshfileprefix\" is missing\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    } catch (nlohmann::detail::type_error) {
      std::cerr << "Error while parsing ASTE configuration file \"meshfileprefix\" is missing or not a string\n";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

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
