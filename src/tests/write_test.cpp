#include "testing.hpp"

void writetest(const Case &current_case)
{
  using VID = aste::Mesh::VID;

  aste::Mesh testMesh;
  testMesh.positions.reserve(12);

  // Points for Quads and Tri Elements
  for (double y = 0; y < 3.0; ++y) {
    for (double x = 0; x < 3.0; ++x) {
      const std::array<double, 3> pos{x, y, 0.0};
      testMesh.positions.push_back(pos);
    }
  }
  //Points for Line Elements
  for (double x = 4; x < 7.0; ++x) {
    const std::array<double, 3> pos{x, 0.0, 0.0};
    testMesh.positions.push_back(pos);
  }

  //Create Lines
  std::array<VID, 2> line1{9, 10};
  std::array<VID, 2> line2{10, 11};
  testMesh.edges.push_back(line1);
  testMesh.edges.push_back(line2);

  // Create Triangles
  std::array<VID, 3> tri1{0, 1, 3};
  std::array<VID, 3> tri2{1, 4, 3};
  std::array<VID, 3> tri3{1, 2, 4};
  std::array<VID, 3> tri4{2, 4, 5};
  testMesh.triangles.push_back(tri1);
  testMesh.triangles.push_back(tri2);
  testMesh.triangles.push_back(tri3);
  testMesh.triangles.push_back(tri4);

  //Create Quad Elements
  std::array<VID, 4> quad1{3, 4, 7, 6};
  std::array<VID, 4> quad2{4, 5, 8, 7};
  testMesh.quadrilaterals.push_back(quad1);
  testMesh.quadrilaterals.push_back(quad2);

  testMesh.data.resize(testMesh.positions.size() * current_case.dim);
  std::iota(testMesh.data.begin(), testMesh.data.end(), 0);
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
}
