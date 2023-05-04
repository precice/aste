#include "modes.hpp"
#include <iostream>
#include "logger.hpp"
#include "utilities.hpp"

void aste::runReplayMode(const aste::ExecutionContext &context, const std::string &asteConfigName)
{
  aste::asteConfig asteConfiguration;
  asteConfiguration.load(asteConfigName);
  const std::string participantName = asteConfiguration.participantName;
  addLogIdentity(participantName, context.rank);
  ASTE_INFO << "ASTE Running in replay mode";

  precice::SolverInterface preciceInterface(participantName, asteConfiguration.preciceConfigFilename, context.rank, context.size);

  size_t           minMeshSize{0};
  std::vector<int> vertexIDs;
  double           dt;

  for (auto &asteInterface : asteConfiguration.asteInterfaces) {
    const std::string meshname = asteInterface.meshFilePrefix;
    asteInterface.meshes       = aste::BaseName(meshname).findAll(context);
    if (asteInterface.meshes.empty()) {
      ASTE_ERROR << "ERROR: Could not find meshes for name: " << meshname;
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    for (const auto &dataname : asteInterface.writeVectorNames) {
      const int dim = preciceInterface.getDataDimensions(asteInterface.meshName, dataname);
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::WRITE, dim, dataname);

#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
      if (preciceInterface.requiresGradientDataFor(asteInterface.meshName, dataname)) {
        asteInterface.writeVectorNames.push_back(dataname + "_gradient");
        asteInterface.mesh.meshdata.emplace_back(aste::datatype::GRADIENT, dim, dataname, dim);
      }
#endif
    }

    for (const auto &dataname : asteInterface.readVectorNames) {
      const int dim = preciceInterface.getDataDimensions(asteInterface.meshName, dataname);
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::READ, dim, dataname);
    }

    for (const auto &dataname : asteInterface.writeScalarNames) {
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::WRITE, 1, dataname);

#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
      if (preciceInterface.requiresGradientDataFor(asteInterface.meshName, dataname)) {
        const int dim = preciceInterface.getMeshDimensions(asteInterface.meshName);
        asteInterface.writeVectorNames.push_back(dataname + "_gradient");
        asteInterface.mesh.meshdata.emplace_back(aste::datatype::GRADIENT, 1, dataname, dim);
      }
#endif
    }
    for (const auto &dataname : asteInterface.readScalarNames) {
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::READ, 1, dataname);
    }

    ASTE_INFO << "Loading mesh from " << asteInterface.meshes.front().filename();
    const bool requireConnectivity = preciceInterface.requiresMeshConnectivityFor(asteInterface.meshName);
    const int  dim                 = preciceInterface.getMeshDimensions(asteInterface.meshName);
    asteInterface.meshes.front().loadMesh(asteInterface.mesh, dim, requireConnectivity);
    ASTE_INFO << "The loaded mesh " << asteInterface.meshes.front().filename() << " contains: " << asteInterface.mesh.summary();
    vertexIDs = setupMesh(preciceInterface, asteInterface.mesh, asteInterface.meshName);
    ASTE_DEBUG << "Mesh setup completed on Rank " << context.rank;
    minMeshSize = std::max(minMeshSize, asteInterface.meshes.size());
  }

  std::size_t round{0};

  ASTE_DEBUG << "Looking for dt = " << asteConfiguration.startdt;
  for (const auto &mesh : asteConfiguration.asteInterfaces.front().meshes) {
    if (mesh.filename().find(std::to_string(asteConfiguration.startdt)) == std::string::npos)
      round++;
    else
      break;
  }
  ASTE_DEBUG << "Found in position " << round << "\n";
  ASTE_INFO << "ASTE Start mesh is " << asteConfiguration.asteInterfaces.front().meshes[round].filename();
  ASTE_INFO << "ASTE Final mesh is " << asteConfiguration.asteInterfaces.front().meshes.back().filename();

  if (preciceInterface.requiresInitialData()) {
    if (round == 0) {
      ASTE_ERROR << "Starting from dt = " << std::to_string(asteConfiguration.startdt) << " but previous timestep \".init\" or " << std::to_string(asteConfiguration.startdt - 1) << " was not found. Please make sure the relevant Mesh exists.";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    ASTE_INFO << "Write initial data for participant " << participantName;
    for (auto &asteInterface : asteConfiguration.asteInterfaces) {
      asteInterface.meshes[round - 1].loadData(asteInterface.mesh);
      ASTE_INFO << "The mesh contains: " << asteInterface.mesh.summary();
      for (const auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::WRITE) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size());
            preciceInterface.writeBlockScalarData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            preciceInterface.writeBlockVectorData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
        }
      }
      ASTE_DEBUG << "Data written: " << asteInterface.mesh.previewData();
    }
  }

  dt = preciceInterface.initialize();

  while (preciceInterface.isCouplingOngoing() && (round < minMeshSize)) {
    if (preciceInterface.requiresWritingCheckpoint()) {
      ASTE_ERROR << "Implicit coupling schemes cannot be used with ASTE";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    for (auto &asteInterface : asteConfiguration.asteInterfaces) {
      ASTE_INFO << "Read mesh for t= " << round << " from " << asteInterface.meshes[round];
      asteInterface.meshes[round].resetData(asteInterface.mesh);
      asteInterface.meshes[round].loadData(asteInterface.mesh);
      ASTE_DEBUG << "This roundmesh contains: " << asteInterface.mesh.summary();

      for (const auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::WRITE) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size());
            preciceInterface.writeBlockScalarData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            preciceInterface.writeBlockVectorData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
        }
#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
        else if (meshdata.type == aste::datatype::GRADIENT) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            // preciceInterface.writeBlockScalarData(meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            preciceInterface.writeBlockScalarGradientData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim * dim);
            preciceInterface.writeBlockVectorGradientData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
        }
#endif
        ASTE_DEBUG << "Data written: " << asteInterface.mesh.previewData(meshdata);
      }
    }
    dt = preciceInterface.advance(dt);
    if (preciceInterface.requiresReadingCheckpoint()) {
      ASTE_ERROR << "Implicit coupling schemes cannot be used with ASTE";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    for (auto &asteInterface : asteConfiguration.asteInterfaces) {
      for (auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::READ) {
          switch (meshdata.numcomp) {
          case 1:
            meshdata.dataVector.resize(vertexIDs.size());
            preciceInterface.readBlockScalarData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            meshdata.dataVector.resize(vertexIDs.size() * dim);
            preciceInterface.readBlockVectorData(asteInterface.meshName, meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
          ASTE_DEBUG << "Data read: " << asteInterface.mesh.previewData(meshdata);
        }
      }
    }
    round++;
  }
  preciceInterface.finalize();
};

void aste::runMapperMode(const aste::ExecutionContext &context, const OptionMap &options)
{
  const std::string meshname        = options["mesh"].as<std::string>();
  const std::string participantName = options["participant"].as<std::string>();
  const std::string dataname        = options["data"].as<std::string>();
  const bool        isVector        = options["vector"].as<bool>();
  const std::string preciceConfig   = options["precice-config"].as<std::string>();

  addLogIdentity(participantName, context.rank);
  ASTE_INFO << "ASTE Running in mapping test mode";

  aste::asteConfig asteConfiguration;

  // Create and configure solver interface
  precice::SolverInterface preciceInterface(participantName, preciceConfig, context.rank, context.size);

  if (participantName == "A") {
    asteConfiguration.participantName       = "A";
    asteConfiguration.preciceConfigFilename = preciceConfig;
    aste::asteInterface asteInterface;
    asteInterface.meshName       = "A-Mesh";
    asteInterface.meshFilePrefix = meshname;
    asteInterface.meshes         = aste::BaseName(meshname).findAll(context);

    if (isVector) {
      asteInterface.writeVectorNames.push_back("Data");
      const int dim = preciceInterface.getDataDimensions(meshname, dataname);
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::WRITE, dim, dataname);

#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
      if (preciceInterface.requiresGradientDataFor(asteInterface.meshName, "Data")) {
        asteInterface.writeVectorNames.push_back(dataname + "_gradient");
        asteInterface.mesh.meshdata.emplace_back(aste::datatype::GRADIENT, dim, dataname, dim);
      }
#endif
    } else {
      asteInterface.writeScalarNames.push_back("Data");
      const int dim = preciceInterface.getMeshDimensions(meshname);
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::WRITE, 1, dataname);

#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
      if (preciceInterface.requiresGradientDataFor(asteInterface.meshName, "Data")) {
        asteInterface.writeVectorNames.push_back(dataname + "_gradient");
        asteInterface.mesh.meshdata.emplace_back(aste::datatype::GRADIENT, 1, dataname, dim);
      }
#endif
    }
    asteConfiguration.asteInterfaces.push_back(asteInterface);
  } else if (participantName == "B") {
    asteConfiguration.participantName       = "B";
    asteConfiguration.preciceConfigFilename = preciceConfig;
    aste::asteInterface asteInterface;
    asteInterface.meshName       = "B-Mesh";
    asteInterface.meshFilePrefix = meshname;
    asteInterface.meshes         = aste::BaseName(meshname).findAll(context);

    if (isVector) {
      asteInterface.writeVectorNames.push_back("Data");
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::READ, dim, dataname);
    } else {
      asteInterface.writeScalarNames.push_back("Data");
      asteInterface.mesh.meshdata.emplace_back(aste::datatype::READ, 1, dataname);
    }
    asteConfiguration.asteInterfaces.push_back(asteInterface);
  }

  auto asteInterface = asteConfiguration.asteInterfaces.front();
  ASTE_INFO << "Loading mesh from " << asteInterface.meshes.front().filename();
  const bool requireConnectivity = preciceInterface.requiresMeshConnectivityFor(asteInterface.meshName);
  const int  dim                 = preciceInterface.getMeshDimensions(asteInterface.meshName);
  asteInterface.meshes.front().loadMesh(asteInterface.mesh, dim, requireConnectivity);
  asteInterface.meshes.front().loadData(asteInterface.mesh);
  ASTE_INFO << "The loaded mesh " << asteInterface.meshes.front().filename() << " contains: " << asteInterface.mesh.summary();
  auto vertexIDs = aste::setupMesh(preciceInterface, asteInterface.mesh, asteInterface.meshName);
  ASTE_DEBUG << "Mesh setup completed on Rank " << context.rank;

  if (preciceInterface.requiresInitialData()) {
    ASTE_DEBUG << "Write initial data for participant " << participantName;
    for (auto const &asteInterface : asteConfiguration.asteInterfaces) {
      for (const auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::WRITE) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size());
            preciceInterface.writeBlockScalarData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            preciceInterface.writeBlockVectorData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
        }
#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
        else if (meshdata.type == aste::datatype::GRADIENT) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            // preciceInterface.writeBlockScalarData(meshdata.name, vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            preciceInterface.writeBlockScalarGradientData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim * dim);
            preciceInterface.writeBlockVectorGradientData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
        }
#endif
      }
      ASTE_DEBUG << "Data written: " << asteInterface.mesh.previewData();
    }
  }

  double dt = preciceInterface.initialize();

  size_t round = 0;

  while (preciceInterface.isCouplingOngoing() && round < asteInterface.meshes.size()) {
    if (preciceInterface.requiresWritingCheckpoint()) {
      ASTE_ERROR << "Implicit coupling schemes cannot be used with ASTE";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    for (auto &asteInterface : asteConfiguration.asteInterfaces) {
      ASTE_INFO << "Read mesh for t=" << round << " from " << asteInterface.meshes[round];
      asteInterface.meshes[round].resetData(asteInterface.mesh);
      asteInterface.meshes[round].loadData(asteInterface.mesh);
      ASTE_DEBUG << "This roundmesh contains: " << asteInterface.mesh.summary();

      for (const auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::WRITE) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size());
            preciceInterface.writeBlockScalarData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            preciceInterface.writeBlockVectorData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
          ASTE_DEBUG << "Data written: " << asteInterface.mesh.previewData(meshdata);
        }
#if PRECICE_VERSION_GREATER_EQUAL(2, 5, 0)
        else if (meshdata.type == aste::datatype::GRADIENT) {
          switch (meshdata.numcomp) {
          case 1:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim);
            preciceInterface.writeBlockScalarGradientData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            assert(meshdata.dataVector.size() == vertexIDs.size() * dim * dim);
            preciceInterface.writeBlockVectorGradientData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
          ASTE_DEBUG << "Gradient data written: " << asteInterface.mesh.previewData(meshdata);
        }
#endif
      }
    }
    dt = preciceInterface.advance(dt);
    if (preciceInterface.requiresReadingCheckpoint()) {
      ASTE_ERROR << "Implicit coupling schemes cannot be used with ASTE";
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    for (auto &asteInterface : asteConfiguration.asteInterfaces) {
      for (auto &meshdata : asteInterface.mesh.meshdata) {
        if (meshdata.type == aste::datatype::READ) {
          switch (meshdata.numcomp) {
          case 1:
            meshdata.dataVector.resize(vertexIDs.size());
            preciceInterface.readBlockScalarData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          default:
            meshdata.dataVector.resize(vertexIDs.size() * dim);
            preciceInterface.readBlockVectorData(asteInterface.meshName, "Data", vertexIDs.size(), vertexIDs.data(), meshdata.dataVector.data());
            break;
          }
          ASTE_DEBUG << "Data read: " << asteInterface.mesh.previewData(meshdata);
        }
      }
    }
    round++;
  }

  // Write out results in same format as data was read
  if (asteConfiguration.participantName == "B") {
    auto meshname = asteConfiguration.asteInterfaces.front().meshes.front();
    auto filename = fs::path(options["output"].as<std::string>());
    if (context.rank == 0 && fs::exists(filename)) {
      if (context.isParallel() && !filename.parent_path().empty()) {
        auto dir = filename.parent_path();
        fs::remove_all(dir);
        fs::create_directory(dir);
      } else if (!context.isParallel()) {
        fs::remove(filename);
      }
    }
    MPI_Barrier(MPI_COMM_WORLD);
    //
    ASTE_INFO << "Writing results to " << options["output"].as<std::string>();
    meshname.save(asteConfiguration.asteInterfaces.front().mesh, options["output"].as<std::string>());
  }
  preciceInterface.finalize();
  return;
}
