#include <mesh.hpp>
#include <numeric>
#include <stdexcept>

int main(int argc, char *argv[])
{
  //if (argc != 2) {
  //  throw std::invalid_argument("Usage is ./executable test_type");
  //  return 1;
  //}

  auto test_name = std::string{argv[1]};

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
  std::array<size_t, 2> line1{9, 10};
  std::array<size_t, 2> line2{10, 11};
  testMesh.edges.push_back(line1);
  testMesh.edges.push_back(line2);

  // Create Triangles
  std::array<size_t, 3> tri1{0, 1, 3};
  std::array<size_t, 3> tri2{1, 4, 3};
  std::array<size_t, 3> tri3{1, 2, 4};
  std::array<size_t, 3> tri4{2, 4, 5};
  testMesh.triangles.push_back(tri1);
  testMesh.triangles.push_back(tri2);
  testMesh.triangles.push_back(tri3);
  testMesh.triangles.push_back(tri4);

  //Create Quad Elements
  std::array<size_t, 4> quad1{3, 4, 7, 6};
  std::array<size_t, 4> quad2{4, 5, 8, 7};
  testMesh.quadrilaterals.push_back(quad1);
  testMesh.quadrilaterals.push_back(quad2);

  if (test_name == "scalar") {
    //Create Scalar Data
    testMesh.data.resize(testMesh.positions.size());
    std::iota(testMesh.data.begin(), testMesh.data.end(), 0);
    auto scalar_test = aste::BaseName{"write_test_scalars"}.with(aste::ExecutionContext());
    scalar_test.save(testMesh, "Scalars");
  } else if (test_name == "vector2d") {
    // Create 2D Vector Data
    testMesh.data.resize(testMesh.positions.size() * 2);
    std::iota(testMesh.data.begin(), testMesh.data.end(), 0);
    auto vector2d_test = aste::BaseName{"write_test_vector2d"}.with(aste::ExecutionContext());
    vector2d_test.save(testMesh, "Vector2D");
  } else if (test_name == "vector3d") {
    // Create 3D Vector Data
    testMesh.data.resize(testMesh.positions.size() * 3);
    std::iota(testMesh.data.begin(), testMesh.data.end(), 0);
    auto vector3d_test = aste::BaseName{"write_test_vector3d"}.with(aste::ExecutionContext());
    vector3d_test.save(testMesh, "Vector3D");
  } else {
    throw std::invalid_argument("Invalid Test Type. Valid Test Types : scalar vector2d vector3d");
    return 1;
  }
}
