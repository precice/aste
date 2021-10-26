#include <boost/test/unit_test.hpp>
#include <mesh.hpp>
#include <numeric>
#include <string>

struct Case {
  std::string fname{};
  std::string dataname{};
  int         dim{};
};

void writetest(const Case &current_case);
void readtest(const Case &current_case);
