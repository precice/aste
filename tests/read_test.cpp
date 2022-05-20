#include "testing.hpp"

void readtest(const ReadCase &current_case)
{

  auto       read_test = aste::BaseName{current_case.fname}.with(aste::ExecutionContext());
  aste::Mesh mesh;
  read_test.loadMesh(mesh, current_case.dim, true);

  BOOST_TEST(mesh.positions.size() == 12);
  BOOST_TEST(mesh.edges.size() == 2);
  if (current_case.dim == 3) {
    BOOST_TEST(mesh.quadrilaterals.size() == 2);
    BOOST_TEST(mesh.triangles.size() == 4);
  }
  // std::cout << "Number of mesh elements are correctly loaded\n";

  BOOST_TEST(mesh.edges[1][0] == 10);
  BOOST_TEST(mesh.edges[1][1] == 11);
  // std::cout << "Edges loaded correctly\n";
  if (current_case.dim == 3) {
    BOOST_TEST(mesh.triangles[0][0] == 0);
    BOOST_TEST(mesh.triangles[0][1] == 1);
    BOOST_TEST(mesh.triangles[0][2] == 3);
    // std::cout << "Triangles loaded correctly\n";
    BOOST_TEST(mesh.quadrilaterals[1][0] == 4);
    BOOST_TEST(mesh.quadrilaterals[1][1] == 5);
    BOOST_TEST(mesh.quadrilaterals[1][2] == 8);
    BOOST_TEST(mesh.quadrilaterals[1][3] == 7);
  }
  // std::cout << "Quads loaded correctly\n";
  aste::MeshData caseData(aste::datatype::WRITE, current_case.dim, current_case.dataname, 1);
  mesh.meshdata.push_back(caseData);
  read_test.loadData(mesh);
  switch (current_case.dim) {
  case 1:
    BOOST_TEST(mesh.meshdata.front().dataVector.size() == 12);
    break;
  case 2:
    BOOST_TEST(mesh.meshdata.front().dataVector.size() == 24);
    break;
  case 3:
    BOOST_TEST(mesh.meshdata.front().dataVector.size() == 36);
    break;
  }

  std::vector<double> testdata;
  testdata.resize(mesh.meshdata.front().dataVector.size());

  std::iota(testdata.begin(), testdata.end(), 0);

  for (size_t i = 0; i < mesh.meshdata.front().dataVector.size(); ++i) {
    BOOST_TEST(mesh.meshdata.front().dataVector[i] == testdata[i]);
  }
}