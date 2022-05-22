#include <boost/filesystem.hpp>
#include <boost/filesystem/operations.hpp>
#include <cstdlib>

#include "testing.hpp"

namespace fs = boost::filesystem;

void writetest(const WriteCase &current_case)
{

  auto       write_test = aste::BaseName{current_case.basename}.with(aste::ExecutionContext());
  aste::Mesh testMesh;
  write_test.loadMesh(testMesh, current_case.dim, current_case.connectivity);
  aste::MeshData caseData(aste::datatype::WRITE, current_case.dim, current_case.dataname, 1);
  testMesh.meshdata.push_back(caseData);
  write_test.loadData(testMesh);

  // Create a new data (mapped) and changeg with old one
  // Use random starting point for a series of data
  testMesh.meshdata.front().dataVector.resize(testMesh.positions.size() * current_case.dim);
  std::iota(testMesh.meshdata.front().dataVector.begin(), testMesh.meshdata.front().dataVector.end(), rand());

  auto scalar_test = aste::BaseName{"write_test"}.with(aste::ExecutionContext());
  scalar_test.save(testMesh, "write_test");

  // Read written data and compare with created data
  auto       read = aste::BaseName{"write_test"}.with(aste::ExecutionContext());
  aste::Mesh testMeshRead;
  read.loadMesh(testMeshRead, current_case.dim, current_case.connectivity);
  testMeshRead.meshdata.push_back(caseData);
  read.loadData(testMeshRead);

  // Check Elements are correctly written
  BOOST_TEST(testMeshRead.positions.size() == testMesh.positions.size());
  if (current_case.connectivity) {
    BOOST_TEST(testMeshRead.edges.size() == testMesh.edges.size());
  }
  if (current_case.dim == 3 && current_case.connectivity) {
    BOOST_TEST(testMeshRead.quadrilaterals.size() == testMesh.quadrilaterals.size());
    BOOST_TEST(testMeshRead.triangles.size() == testMesh.triangles.size());
  }
  // Check Edges
  if (current_case.connectivity) {
    BOOST_TEST(testMeshRead.edges[1][0] == testMesh.edges[1][0]);
    BOOST_TEST(testMeshRead.edges[1][1] == testMesh.edges[1][1]);
  }
  if (current_case.dim == 3 && current_case.connectivity) {
    // Check Triangles
    BOOST_TEST(testMeshRead.triangles[0][0] == testMesh.triangles[0][0]);
    BOOST_TEST(testMeshRead.triangles[0][1] == testMesh.triangles[0][1]);
    BOOST_TEST(testMeshRead.triangles[0][2] == testMesh.triangles[0][2]);
    // Check Quads
    BOOST_TEST(testMeshRead.quadrilaterals[1][0] == testMesh.quadrilaterals[1][0]);
    BOOST_TEST(testMeshRead.quadrilaterals[1][1] == testMesh.quadrilaterals[1][1]);
    BOOST_TEST(testMeshRead.quadrilaterals[1][2] == testMesh.quadrilaterals[1][2]);
    BOOST_TEST(testMeshRead.quadrilaterals[1][3] == testMesh.quadrilaterals[1][3]);
  }
  // Check Datasize
  BOOST_TEST(testMeshRead.meshdata.front().dataVector.size() == testMesh.meshdata.front().dataVector.size());
  // Check Data Values
  for (size_t i = 0; i < testMeshRead.meshdata.front().dataVector.size(); ++i) {
    BOOST_TEST(testMeshRead.meshdata.front().dataVector[i] == testMesh.meshdata.front().dataVector[i]);
  }

  // Remove Artifacts
  if (fs::is_regular_file(current_case.fname + ".vtk")) {
    fs::remove(current_case.fname + ".vtk");
  }
  if (fs::is_regular_file("write_test.vtk")) {
    fs::remove("write_test.vtk");
  }
}
