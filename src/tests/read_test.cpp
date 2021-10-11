#include <iostream>
#include <mesh.hpp>
#include <numeric>

int main(int argc, char *argv[])
{

  auto filename = std::string{argv[1]};
  auto dim      = std::stoi(argv[2]);
  auto dataname = std::string{argv[3]};

  auto read_test = aste::BaseName{filename}.with(aste::ExecutionContext());
  auto mesh      = read_test.load(dim, dataname);

  assert(mesh.positions.size() == 12);
  assert(mesh.edges.size() == 2);
  assert(mesh.quadrilaterals.size() == 2);
  assert(mesh.triangles.size() == 4);
  std::cout << "Number of mesh elements are correctly loaded\n";

  assert(mesh.edges[1][0] == 10);
  assert(mesh.edges[1][1] == 11);
  std::cout << "Edges loaded correctly\n";
  assert(mesh.triangles[0][0] == 0);
  assert(mesh.triangles[0][1] == 1);
  assert(mesh.triangles[0][2] == 3);
  std::cout << "Triangles loaded correctly\n";
  assert(mesh.quadrilaterals[1][0] == 4);
  assert(mesh.quadrilaterals[1][1] == 5);
  assert(mesh.quadrilaterals[1][2] == 8);
  assert(mesh.quadrilaterals[1][3] == 7);
  std::cout << "Quads loaded correctly\n";

  switch (dim) {
  case 1:
    assert(mesh.data.size() == 12);
    break;
  case 2:
    assert(mesh.data.size() == 24);
    break;
  case 3:
    assert(mesh.data.size() == 36);
    break;
  }

  std::vector<double> testdata;
  testdata.resize(mesh.data.size());

  std::iota(testdata.begin(), testdata.end(), 0);

  for (size_t i = 0; i < mesh.data.size(); ++i) {
    assert(mesh.data[i] == testdata[i]);
  }

  return 0;
}
