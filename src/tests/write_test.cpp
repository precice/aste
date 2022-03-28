#include <boost/filesystem.hpp>
#include <boost/filesystem/operations.hpp>
#include <cstdlib>

#include "testing.hpp"

namespace fs = boost::filesystem;

void writetest(const WriteCase &current_case)
{

  auto write_test = aste::BaseName{current_case.basename}.with(aste::ExecutionContext());
  auto testMesh   = write_test.load(current_case.dim, current_case.dataname);

  // Create a new data (mapped) and changeg with old one
  // Use random starting point for a series of data
  testMesh.data.resize(testMesh.positions.size() * current_case.dim);
  std::iota(testMesh.data.begin(), testMesh.data.end(), rand());

  auto scalar_test = aste::BaseName{current_case.fname}.with(aste::ExecutionContext());
  scalar_test.save(testMesh, current_case.dataname);

  // Read written data and compare with created data
  auto read       = aste::BaseName{current_case.fname}.with(aste::ExecutionContext());
  auto loadedMesh = read.load(current_case.dim, current_case.dataname);

  //Check Elements are correctly written
  BOOST_TEST(loadedMesh.positions.size() == testMesh.positions.size());
  BOOST_TEST(loadedMesh.edges.size() == testMesh.edges.size());
  BOOST_TEST(loadedMesh.quadrilaterals.size() == testMesh.quadrilaterals.size());
  BOOST_TEST(loadedMesh.triangles.size() == testMesh.triangles.size());
  //Check Edges
  BOOST_TEST(loadedMesh.edges[1][0] == testMesh.edges[1][0]);
  BOOST_TEST(loadedMesh.edges[1][1] == testMesh.edges[1][1]);
  //Check Triangles
  BOOST_TEST(loadedMesh.triangles[0][0] == testMesh.triangles[0][0]);
  BOOST_TEST(loadedMesh.triangles[0][1] == testMesh.triangles[0][1]);
  BOOST_TEST(loadedMesh.triangles[0][2] == testMesh.triangles[0][2]);
  //Check Quads
  BOOST_TEST(loadedMesh.quadrilaterals[1][0] == testMesh.quadrilaterals[1][0]);
  BOOST_TEST(loadedMesh.quadrilaterals[1][1] == testMesh.quadrilaterals[1][1]);
  BOOST_TEST(loadedMesh.quadrilaterals[1][2] == testMesh.quadrilaterals[1][2]);
  BOOST_TEST(loadedMesh.quadrilaterals[1][3] == testMesh.quadrilaterals[1][3]);
  //Check Datasize
  BOOST_TEST(loadedMesh.data.size() == testMesh.data.size());
  //Check Data Values
  for (size_t i = 0; i < loadedMesh.data.size(); ++i) {
    BOOST_TEST(loadedMesh.data[i] == testMesh.data[i]);
  }

  //Remove Artifacts
  std::cout << current_case.fname << std::endl;
  if (fs::is_regular_file(current_case.fname + ".vtk")) {
    fs::remove(current_case.fname + ".vtk");
  }
}
