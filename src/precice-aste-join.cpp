#include "precice-aste-join.hpp"

auto getOptions(int argc, char *argv[]) -> OptionMap
{
  namespace po = boost::program_options;

  // Declare the supported options.
  po::options_description desc("Allowed options");
  desc.add_options()("help", "produce help message")("mesh,m", po::value<std::string>(), "The partitioned mesh prefix used as input (only VTU format is accepted)(Looking for <prefix>_<#filerank>.vtu).")("output,o", po::value<std::string>(), "The output mesh. Can be VTK or VTU format. If it is not given <inputmesh>_joined.vtk will be used.")("recovery,r", po::value<std::string>(), "The path to the recovery file to fully recover it's state.")("numparts,n", po::value<size_t>()->default_value(0), "The number of parts to read from the input mesh. By default the entire mesh is read.")("directory,dir", po::value<std::string>()->default_value("."), "Directory for output files (optional)");

  po::variables_map vm;
  try {
    po::store(parse_command_line(argc, argv, desc), vm);

    if (vm.count("help")) {
      std::cout << desc << std::endl;
      std::exit(EXIT_SUCCESS);
    }
    // Needs to be called
    po::notify(vm);

    if (!vm.count("mesh")) {
      std::cout << "You must specify a mesh file to read from." << std::endl;
      std::exit(EXIT_SUCCESS);
    }

  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    std::cerr << desc << std::endl;
    std::exit(EXIT_FAILURE);
  }
  return vm;
}

void readRecoveryFile(const std::string &recoveryFile, int &size, std::vector<int> &cellTypes, std::vector<std::vector<int>> &cells)
{
  // Parse the file
  std::ifstream ifs(recoveryFile);
  json          recoveryData = json::parse(ifs);
  //  Get content
  try {
    size = recoveryData["size"].get<int>();
  } catch (nlohmann::detail::parse_error &) {
    std::cerr << "Error while parsing recovery file \"size\" is missing";
    std::exit(EXIT_FAILURE);
  } catch (nlohmann::detail::type_error &) {
    std::cerr << "Error while parsing recovery file \"size\" is missing";
    std::exit(EXIT_FAILURE);
  }

  try {
    cellTypes = recoveryData["cell_types"].get<std::vector<int>>();
  } catch (nlohmann::detail::parse_error &) {
    std::cerr << "Error while parsing recovery file \"cell_types\" is missing";
    std::exit(EXIT_FAILURE);
  } catch (nlohmann::detail::type_error &) {
    std::cerr << "Error while parsing recovery file \"cell_types\" is missing";
    std::exit(EXIT_FAILURE);
  }

  try {
    cells = recoveryData["cells"].get<std::vector<std::vector<int>>>();
  } catch (nlohmann::detail::parse_error &) {
    std::cerr << "Error while parsing recovery file \"cells\" is missing";
    std::exit(EXIT_FAILURE);
  } catch (nlohmann::detail::type_error &) {
    std::cerr << "Error while parsing recovery file \"cells\" is missing";
    std::exit(EXIT_FAILURE);
  }
}

auto countPartitions(const std::string &prefix) -> size_t
{
  namespace fs = boost::filesystem;

  std::string filename;
  size_t      count = 0;

  while (true) {
    filename = prefix + "_" + std::to_string(count) + ".vtu";
    if (!fs::exists(filename)) {
      break;
    }
    ++count;
  }
  return count;
}

void writeMesh(const std::string &filename, const std::string &directory, vtkSmartPointer<vtkUnstructuredGrid> mesh)
{
  namespace fs = boost::filesystem;
  if (fs::exists(directory)) {
    if (!fs::is_directory(directory)) {
      std::cerr << "Error: " << directory << " is not a directory." << std::endl;
      std::exit(EXIT_FAILURE);
    }
  } else {
    if (!fs::create_directory(directory)) {
      std::cerr << "Error: Could not create directory " << directory << std::endl;
      std::exit(EXIT_FAILURE);
    }
  }

  auto output_path     = fs::current_path() / fs::path(directory) / fs::path(filename);
  auto output_filename = output_path.c_str();

  if (fs::extension(output_filename) == ".vtu") {
    vtkSmartPointer<vtkXMLUnstructuredGridWriter> writer = vtkSmartPointer<vtkXMLUnstructuredGridWriter>::New();
    writer->SetFileName(output_filename);
    writer->SetInputData(mesh);
    writer->Write();
  } else if (fs::extension(filename) == ".vtk") {
    vtkSmartPointer<vtkUnstructuredGridWriter> writer = vtkSmartPointer<vtkUnstructuredGridWriter>::New();
    writer->SetFileName(output_filename);
    writer->SetInputData(mesh);
    writer->SetFileTypeToBinary();
    writer->Write();
  } else {
    std::cerr << "Error: " << filename << " is not a valid output file." << std::endl;
    std::exit(EXIT_FAILURE);
  }
}

auto partitionwiseMerge(const std::string &prefix, size_t numparts) -> vtkSmartPointer<vtkUnstructuredGrid>
{
  auto joinedMesh   = vtkSmartPointer<vtkUnstructuredGrid>::New();
  auto joinedPoints = vtkSmartPointer<vtkPoints>::New();
  joinedPoints->SetDataTypeToDouble();
  auto             joinedCells = vtkSmartPointer<vtkCellArray>::New();
  std::vector<int> joinedCellTypes;

  std::vector<vtkSmartPointer<vtkDoubleArray>> joinedDataVec;
  std::vector<std::string>                     joinedDatanames;

  auto reader = vtkSmartPointer<vtkXMLUnstructuredGridReader>::New();
  for (size_t i = 0; i < numparts; ++i) {
    // Read mesh
    auto partname = prefix + "_" + std::to_string(i) + ".vtu";
    reader->SetFileName(partname.c_str());
    reader->Update();
    // Extract mesh
    auto grid = reader->GetOutput();
    // Cells
    const auto offset   = joinedPoints->GetNumberOfPoints();
    auto       numCells = grid->GetCells()->GetNumberOfCells();
    joinedCellTypes.reserve(joinedCellTypes.size() + numCells);
    auto cellIds = vtkSmartPointer<vtkIdList>::New();
    for (int j = 0; j < numCells; ++j) {
      cellIds->Reset();
      std::for_each(grid->GetCell(j)->GetPointIds()->begin(), grid->GetCell(j)->GetPointIds()->end(), [&cellIds, &offset](auto &pointId) { cellIds->InsertNextId(pointId + offset); });
      joinedCells->InsertNextCell(cellIds);
      joinedCellTypes.push_back(grid->GetCellType(j));
    }
    // Points
    auto points = grid->GetPoints();
    joinedPoints->InsertPoints(joinedPoints->GetNumberOfPoints(), grid->GetNumberOfPoints(), 0, points);
    //  Point Data
    auto partPointData = grid->GetPointData();
    auto numArrays     = partPointData->GetNumberOfArrays();
    for (int j = 0; j < numArrays; ++j) {
      auto partData = partPointData->GetArray(j);
      auto name     = partData->GetName();
      if (std::find(joinedDatanames.begin(), joinedDatanames.end(), name) == joinedDatanames.end()) {
        joinedDatanames.emplace_back(name);
        auto newJoinedData = vtkSmartPointer<vtkDoubleArray>::New();
        newJoinedData->SetName(name);
        newJoinedData->SetNumberOfComponents(partData->GetNumberOfComponents());
        joinedDataVec.push_back(newJoinedData);
      }
      auto joinedData = joinedDataVec[j];
      joinedData->InsertTuples(joinedData->GetNumberOfTuples(), partData->GetNumberOfTuples(), 0, partData);
    }
  }

  joinedMesh->SetPoints(joinedPoints);
  for (const auto &data : joinedDataVec) {
    joinedMesh->GetPointData()->AddArray(data);
  }
  joinedMesh->SetCells(joinedCellTypes.data(), joinedCells);

  return joinedMesh;
}

auto recoveryMerge(const std::string &prefix, std::size_t numparts, int size, const std::vector<int> &cellTypes, const std::vector<std::vector<int>> &cells) -> vtkSmartPointer<vtkUnstructuredGrid>
{
  auto joinedMesh   = vtkSmartPointer<vtkUnstructuredGrid>::New();
  auto joinedPoints = vtkSmartPointer<vtkPoints>::New();
  joinedPoints->SetDataTypeToDouble();
  auto             joinedCells = vtkSmartPointer<vtkCellArray>::New();
  std::vector<int> joinedCellTypes;

  joinedPoints->SetNumberOfPoints(size);

  std::vector<vtkSmartPointer<vtkDoubleArray>> joinedDataVec;
  std::vector<std::string>                     joinedDataNames;

  auto reader    = vtkSmartPointer<vtkXMLUnstructuredGridReader>::New();
  auto globalIds = vtkSmartPointer<vtkIdList>::New();
  auto localIds  = vtkSmartPointer<vtkIdList>::New();

  for (size_t i = 0; i < numparts; ++i) {
    globalIds->Reset();
    // Read mesh
    auto partname = prefix + "_" + std::to_string(i) + ".vtu";
    reader->SetFileName(partname.c_str());
    reader->Update();
    // Extract mesh
    auto grid = reader->GetOutput();
    // Points
    auto points = grid->GetPoints();
    // Set local Ids
    localIds->SetNumberOfIds(points->GetNumberOfPoints());
    std::iota(localIds->begin(), localIds->end(), 0);
    //  Extract Global Ids
    auto partPointData  = grid->GetPointData();
    auto globalIdsArray = partPointData->GetArray("GlobalIDs");
    if (globalIdsArray == nullptr) {
      std::cerr << "GlobalIDs not found in " << partname << std::endl;
      std::cout << " Fall back to partitionwise merge" << std::endl;
      return partitionwiseMerge(prefix, numparts);
    } else {
      globalIds->Allocate(globalIdsArray->GetNumberOfTuples());
      for (vtkIdType j = 0; j < globalIdsArray->GetNumberOfTuples(); ++j) {
        globalIds->InsertNextId(static_cast<vtkIdType>(globalIdsArray->GetTuple1(j)));
      }
      joinedPoints->InsertPoints(globalIds, localIds, points);
    }

    // Cells
    auto numCells = grid->GetCells()->GetNumberOfCells();
    joinedCellTypes.reserve(joinedCellTypes.size() + numCells);
    auto cellIds = vtkSmartPointer<vtkIdList>::New();
    for (vtkIdType j = 0; j < numCells; ++j) {
      cellIds->Reset();
      std::for_each(grid->GetCell(j)->GetPointIds()->begin(), grid->GetCell(j)->GetPointIds()->end(), [&cellIds, &globalIds](auto &localPointId) { cellIds->InsertNextId(globalIds->GetId(localPointId)); });
      joinedCells->InsertNextCell(cellIds);
      joinedCellTypes.push_back(grid->GetCellType(j));
    }

    // Point Data
    auto numArrays = partPointData->GetNumberOfArrays();
    for (int j = 0; j < numArrays; ++j) {
      auto partData = partPointData->GetArray(j);
      auto name     = partData->GetName();
      if (std::find(joinedDataNames.begin(), joinedDataNames.end(), name) == joinedDataNames.end()) {
        joinedDataNames.emplace_back(name);
        auto newJoinedData = vtkSmartPointer<vtkDoubleArray>::New();
        newJoinedData->SetName(name);
        newJoinedData->SetNumberOfComponents(partData->GetNumberOfComponents());
        newJoinedData->Allocate(size);
        joinedDataVec.push_back(newJoinedData);
      }
      auto joinedData = joinedDataVec[j];
      joinedData->InsertTuples(globalIds, localIds, partData);
    }
  }

  // Add Recovery cells
  auto numCells = cells.size();
  joinedCellTypes.reserve(joinedCellTypes.size() + numCells);
  auto cellIds = vtkSmartPointer<vtkIdList>::New();
  for (std::size_t i = 0; i < numCells; ++i) {
    cellIds->Reset();
    std::for_each(cells[i].begin(), cells[i].end(), [&cellIds](auto &pointId) { cellIds->InsertNextId(pointId); });
    joinedCells->InsertNextCell(cellIds);
    joinedCellTypes.push_back(cellTypes[i]);
  }

  // Assembly final mesh
  for (const auto &data : joinedDataVec) {
    joinedMesh->GetPointData()->AddArray(data);
  }
  joinedMesh->SetPoints(joinedPoints);
  joinedMesh->SetCells(joinedCellTypes.data(), joinedCells);

  return joinedMesh;
}

void join(int argc, char *argv[])
{
  namespace fs        = boost::filesystem;
  auto        options = getOptions(argc, argv);
  std::string prefix  = options["mesh"].as<std::string>();
  std::string output{};
  std::string recovery{};
  if (options.find("output") == options.end()) {
    output = prefix + "_joined.vtk";
  } else {
    output = options["output"].as<std::string>();
  }
  if (options.find("recovery") != options.end()) {
    recovery = options["recovery"].as<std::string>();
  } else {
    recovery = prefix + "_recovery.json";
  }
  std::string directory = options["directory"].as<std::string>();
  size_t      numparts  = options["numparts"].as<size_t>();

  if (numparts == 0) {
    numparts = countPartitions(prefix);
  }

  vtkSmartPointer<vtkUnstructuredGrid> joinedMesh = nullptr;
  if (fs::exists(recovery)) {
    std::cout << "Recovery file found. Will try to recover the state." << std::endl;
    int                           size;
    std::vector<int>              cellTypes;
    std::vector<std::vector<int>> cells;
    readRecoveryFile(recovery, size, cellTypes, cells);
    joinedMesh = recoveryMerge(prefix, numparts, size, cellTypes, cells);
  } else {
    std::cout << "Recovery file not found. Partition-wise merging will be done." << std::endl;
    joinedMesh = partitionwiseMerge(prefix, numparts);
  }

  writeMesh(output, options["directory"].as<std::string>(), joinedMesh);
}

auto main(int argc, char *argv[]) -> int
{
  join(argc, argv);
  return EXIT_SUCCESS;
}
