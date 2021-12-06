#include "testing.hpp"

void readtest(const ReadCase &current_case)
{

  auto read_test = aste::BaseName{current_case.fname}.with(aste::ExecutionContext());
  auto mesh      = read_test.load(current_case.dim, current_case.dataname);

  BOOST_TEST(mesh.positions.size() == 12);
  BOOST_TEST(mesh.edges.size() == 2);
  BOOST_TEST(mesh.quadrilaterals.size() == 2);
  BOOST_TEST(mesh.triangles.size() == 4);
  //std::cout << "Number of mesh elements are correctly loaded\n";

  BOOST_TEST(mesh.edges[1][0] == 10);
  BOOST_TEST(mesh.edges[1][1] == 11);
  //std::cout << "Edges loaded correctly\n";
  BOOST_TEST(mesh.triangles[0][0] == 0);
  BOOST_TEST(mesh.triangles[0][1] == 1);
  BOOST_TEST(mesh.triangles[0][2] == 3);
  //std::cout << "Triangles loaded correctly\n";
  BOOST_TEST(mesh.quadrilaterals[1][0] == 4);
  BOOST_TEST(mesh.quadrilaterals[1][1] == 5);
  BOOST_TEST(mesh.quadrilaterals[1][2] == 8);
  BOOST_TEST(mesh.quadrilaterals[1][3] == 7);
  //std::cout << "Quads loaded correctly\n";

  switch (current_case.dim) {
  case 1:
    BOOST_TEST(mesh.data.size() == 12);
    break;
  case 2:
    BOOST_TEST(mesh.data.size() == 24);
    break;
  case 3:
    BOOST_TEST(mesh.data.size() == 36);
    break;
  }

  std::vector<double> testdata;
  testdata.resize(mesh.data.size());

  std::iota(testdata.begin(), testdata.end(), 0);

  for (size_t i = 0; i < mesh.data.size(); ++i) {
    BOOST_TEST(mesh.data[i] == testdata[i]);
  }
}