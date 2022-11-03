#pragma once

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>
#include <vtkDoubleArray.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkSmartPointer.h>
#include <vtkUnstructuredGrid.h>
#include <vtkUnstructuredGridWriter.h>
#include <vtkXMLUnstructuredGridReader.h>
#include <vtkXMLUnstructuredGridWriter.h>
#include "json.hpp"

using OptionMap = boost::program_options::variables_map;
using json      = nlohmann::json;

/**
 * @brief Get the Options object from command line arguments
 *
 * @param argc
 * @param argv
 * @return OptionMap
 */
auto getOptions(int argc, char *argv[]) -> OptionMap;

void readRecoveryFile(const std::string &recoveryFile, int &size, std::vector<int> &cellTypes, std::vector<std::vector<int>> &cells);

/**
 * @brief Count the number of partitioned mesh files for given prefix
 *
 * @param prefix
 * @return size_t
 */
auto countPartitions(const std::string &prefix) -> size_t;

/**
 * @ brief Write the joined mesh to a VTK file
 *
 * @param filename
 * @param directory
 * @param mesh
 */
void writeMesh(const std::string &filename, const std::string &directory, vtkSmartPointer<vtkUnstructuredGrid> mesh);

/**
 * @brief Merge the meshes from the partitioned files
 * @details The meshes are merged in the order of the partitioned files
 * @details The cells betwen the meshes are not connected
 * @details The point numbering is not preserved between unpartitioned mesh and the merged mesh
 *
 * @param prefix
 * @param numparts
 * @return vtkSmartPointer<vtkUnstructuredGrid>
 */
auto partitionwiseMerge(const std::string &prefix, size_t numparts) -> vtkSmartPointer<vtkUnstructuredGrid>;

/**
 * @brief Merge the meshes from the partitioned files
 * @details The meshes are merged to recover the original mesh
 * @details All the cells are preserved and connected
 * @details The point numbering is preserved between unpartitioned mesh and the merged mesh
 *
 * @param prefix
 * @param numparts
 * @param size
 * @param cellTypes
 * @param cells
 * @return vtkSmartPointer<vtkUnstructuredGrid>
 */
auto recoveryMerge(const std::string &prefix, std::size_t numparts, int size, const std::vector<int> &cellTypes, const std::vector<std::vector<int>> &cells) -> vtkSmartPointer<vtkUnstructuredGrid>;

/**
 * @brief Read the commandline arguments and merge the meshes to a single mesh
 */
void join(int argc, char *argv[]);
