#pragma once
#include <iostream>
#include <mpi.h>
#include <boost/program_options.hpp>

#include "utils/prettyprint.hpp"

using DistVertex = std::vector<double>;

/// The serialized mesh
using DistMesh = std::vector<DistVertex>;

/// The data, living at each mesh node
using Data = std::vector<double>;

using OptionMap = boost::program_options::variables_map;

OptionMap getOptions(int argc, char *argv[]);

void printOptions(const OptionMap &options);

void printMesh(const DistMesh &mesh, const Data &data, bool verbose);

// Partitions range in equal chunks
template<typename T>
std::vector<T> partition(T& range, int num)
{
  int partSize = range.size() / num;
  std::vector<T> partitions;
  for (int i = 0; i < num; i++) {
    if (i==num-1)
      partitions.emplace_back(range.begin()+(i*partSize), range.end());
    else
      partitions.emplace_back(range.begin()+(i*partSize), range.begin()+((i+1)*partSize));
    
  }
  return partitions;
    
}
