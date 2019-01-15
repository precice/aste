#include <iostream>
#include <string>
#include <boost/filesystem.hpp>
#include <mpi.h>
#include "precice/SolverInterface.hpp"
#include "utils/prettyprint.hpp"
#include "utils/EventTimings.hpp"

#include "common.hpp"
namespace fs = boost::filesystem; 

int numMeshParts(std::string meshname);

int main(int argc, char* argv[])
{
    using std::string;
    MPI_Init(&argc, &argv);
    auto options = getOptions(argc, argv);
    std::string meshname = options["meshFile"].as<string>();
    string participant = options["participant"].as<string>();

    int MPIrank = 0, MPIsize = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &MPIrank);
    MPI_Comm_size(MPI_COMM_WORLD, &MPIsize);

    auto numParts = numMeshParts(meshname);
    if (numParts < MPIsize)
        throw std::runtime_error("Mesh is too small for communicator, MeshSize="  + std::to_string(numParts) + ", Comm_size=" + std::to_string(MPIsize));

    precice::SolverInterface interface(participant, MPIrank, MPIsize);
    interface.configure(options["precice-config"].as<string>());
    precice::utils::EventRegistry::instance().runName = std::string();
    int meshID = interface.getMeshID( (participant == "A") ? "MeshA" : "MeshB" ); // participant = A => MeshID = MeshA
    int dataID = interface.getDataID("Data", meshID);
    std::vector<int> vertexIDs;
    std::vector<double> data;
    std::vector<std::array<double, 3>> positions;
    int i = 0;
    auto filename = meshname + "/" + std::to_string(MPIrank);
    std::ifstream infile(filename);
    double x, y, z, val;
    std::string line;
    while (std::getline(infile, line)){
        std::istringstream iss(line);
        iss >> x >> y >> z >> val;
        std::array<double, 3> vertexPos{x, y, z};
        vertexIDs.push_back(interface.setMeshVertex(meshID, vertexPos.data()));
        positions.push_back(vertexPos);
        if (participant == "A") //val is ignored on B.
            data.push_back(val);
        i++;
    }
    infile.close();
    if (participant == "B")
        data = std::vector<double>(vertexIDs.size(), 0);
    interface.initialize();

    if (interface.isActionRequired(precice::constants::actionWriteInitialData())) {
        std::cout << "Write initial data for participant " << participant << std::endl;
        interface.writeBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
        interface.fulfilledAction(precice::constants::actionWriteInitialData());
    }
    interface.initializeData();

    while (interface.isCouplingOngoing()) {
        if (participant == "A" and not data.empty()) {
            interface.writeBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
        }
        interface.advance(1);

        if (participant == "B") {
            interface.readBlockScalarData(dataID, data.size(), vertexIDs.data(), data.data());
        }
    }

    // Write out results in same format as data was read
    if (participant == "B") {
        std::cout << "=========Write to " << options["output"].as<string>() << std::endl;
        fs::path outfile(options["output"].as<string>());
        fs::create_directory(outfile);
        outfile = outfile / std::to_string(MPIrank);
        std::ofstream ostream(outfile.string(), std::ios::trunc);
        ostream.precision(9);
        for (size_t i = 0; i < data.size(); i++) {
            ostream << positions[i][0] << " " << positions[i][1] << " " << positions[i][2] << " " << data[i] << std::endl;
        }
        ostream.close();
    }

    interface.finalize();
    MPI_Finalize();
}

int numMeshParts(std::string meshname)
{

    if (!fs::is_directory(meshname))
        throw std::runtime_error("Invalid mesh name: directory not found.");
    int i = 0;
    while (fs::exists(meshname + "/" + std::to_string(i)))
        i++;
    return i;
}
