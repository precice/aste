
#define BOOST_TEST_MODULE ASTE
#define BOOST_TEST_DYN_LINK
#include <boost/test/unit_test.hpp>

#include <iostream>
#include <mesh.hpp>
#include <numeric>
#include <string>
#include <vector>

struct Case {
  std::string fname{};
  std::string dataname{};
  int         dim{};
};

std::vector<Case> Cases;

BOOST_AUTO_TEST_SUITE(read_test)

BOOST_AUTO_TEST_CASE(read_test)

{
  //Add Cases Here
  Cases.push_back(Case{"../src/tests/reference_scalars", "Scalars", 1});
  Cases.push_back(Case{"../src/tests/reference_vector2d", "Vector2D", 2});
  Cases.push_back(Case{"../src/tests/reference_vector3d", "Vector3D", 3});

  for (auto current_case : Cases) {
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
} // End of test suite
BOOST_AUTO_TEST_SUITE_END()