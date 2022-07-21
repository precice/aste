#include <boost/test/unit_test.hpp>
#include <mesh.hpp>
#include <numeric>
#include <string>

struct ReadCase {
  std::string fname{};
  std::string dataname{};
  int         dim{};
  bool        connectivity;
};

struct WriteCase {
  std::string basename{};
  std::string fname{};
  std::string dataname{};
  int         dim{};
  bool        connectivity;
};

void writetest(const WriteCase &current_case);
void readtest(const ReadCase &current_case);
