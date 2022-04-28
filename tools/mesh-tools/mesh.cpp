#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <gmsh.h>
#include <iostream>
#include <set>

std::string formatSize(double size)
{
  std::string str = std::to_string(size);
  str.erase(str.find_last_not_of('0') + 1, std::string::npos);
  return str;
}

int main(int argc, char **argv)
{
  if (argc < 3) {
    std::cerr << "Usage: exe INPUT SIZE, [SIZE, ...]\n";
    return 1;
  }

  const std::string input(argv[1]);

  std::vector<double> sizes;
  for (int i = 2; i < argc; ++i) {
    sizes.push_back(std::atof(argv[i]));
  }

  gmsh::initialize(0, nullptr);

  gmsh::vectorpair v;
  try {
    gmsh::model::occ::importShapes(input, v);
  } catch (...) {
    gmsh::logger::write("Could not load STEP file: bye!");
    gmsh::finalize();
    return 0;
  }
  gmsh::model::occ::synchronize();

  gmsh::option::setNumber("Mesh.Algorithm", 5);
  gmsh::option::setNumber("Mesh.SaveAll", 1);
  gmsh::option::setNumber("Mesh.Binary", 1);

  for (double size : sizes) {
    const auto name = formatSize(size);
    std::cout << "= Generating " << name << '\n';
    gmsh::option::setNumber("Mesh.MeshSizeMin", size);
    gmsh::option::setNumber("Mesh.MeshSizeMax", size);
    gmsh::model::mesh::generate(2);
    gmsh::model::mesh::removeDuplicateNodes();
    gmsh::write(name + ".vtk");
    gmsh::model::mesh::clear();
  }

  gmsh::finalize();
  return 0;
}
