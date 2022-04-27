#include <cstdlib>
#include <numeric>
#include <gmsh.h>
#include <iostream>
#include <string>


struct AABB {
  double xmin, ymin, zmin;
  double xmax, ymax, zmax;

  static AABB fromGMSH(const std::pair<int, int>& p) {
    AABB box;
    gmsh::model::occ::getBoundingBox(p.first, p.second, box.xmin, box.ymin, box.zmin, box.xmax, box.ymax, box.zmax);
    return box;
  }

  void print() const {
    std::cout << "x " << xmin << " " << xmax << '\n';
    std::cout << "y " << ymin << " " << ymax << '\n';
    std::cout << "z " << zmin << " " << zmax << '\n';
  }
};

AABB operator+(const AABB& lhs, const AABB& rhs) {
  return {
    std::min(lhs.xmin, rhs.xmin),
    std::min(lhs.ymin, rhs.ymin),
    std::min(lhs.zmin, rhs.zmin),
    std::max(lhs.xmax, rhs.xmax),
    std::max(lhs.ymax, rhs.ymax),
    std::max(lhs.zmax, rhs.zmax)
    };
}

AABB getBoundingBox(const gmsh::vectorpair& v) {
  return std::accumulate(std::next(v.begin()), v.end(), AABB::fromGMSH(v.front()), [](auto last, auto next){ return last + AABB::fromGMSH(next); });
}

int main(int argc, char **argv)
{
  if (argc != 3) {
    std::cerr << "Usage exe INPUT OUTPUT\n";
    return 1;
  }
  const std::string input(argv[1]);
  const std::string output(argv[2]);

  gmsh::initialize(0, nullptr);

  // Load a STEP file (using `importShapes' instead of `merge' allows to
  // directly retrieve the tags of the highest dimensional imported entities):
  gmsh::vectorpair v;
  try {
    gmsh::model::occ::importShapes(input, v);
  } catch(...) {
    gmsh::logger::write("Could not load STEP file: bye!");
    gmsh::finalize();
    return 0;
  }

  // Get the bounding box of the volume:
  const auto box = getBoundingBox(v);

  std::cout << "Initial size\n";
  box.print();

  const auto xd = box.xmax - box.xmin;
  const auto yd = box.ymax - box.ymin;
  const auto zd = box.zmax - box.zmin;
  const auto width = std::max(std::max(xd, yd), zd);
  const auto scale = 1.0/width;
  // Center around origin
  gmsh::model::occ::translate(v, -box.xmin-xd/2, -box.ymin-yd/2, -box.zmin-zd/2);
  // Scale down to unit size
  gmsh::model::occ::dilate(v, 0,0,0 , scale, scale, scale);
  const auto b2 = getBoundingBox(v);
  gmsh::model::occ::translate(v, -b2.xmin, -b2.ymin, -b2.zmin);
  try {
    gmsh::model::occ::removeAllDuplicates();
  } catch (...) {
    std::cerr << "Deduplication failed\n";
  }
  gmsh::model::occ::synchronize();
  gmsh::vectorpair v2;
  gmsh::model::getEntities(v2);
  gmsh::write(output);
  gmsh::finalize();
  return 0;
}
