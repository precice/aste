#define BOOST_TEST_MODULE ASTE
#define BOOST_TEST_DYN_LINK
#include "testing.hpp"

BOOST_AUTO_TEST_SUITE(read_write_tests)

BOOST_AUTO_TEST_CASE(read_test_scalar)
{
  readtest(Case{"../src/tests/reference_scalars", "Scalars", 1});
}

BOOST_AUTO_TEST_CASE(read_test_2dvector)
{
  readtest(Case{"../src/tests/reference_vector2d", "Vector2D", 2});
}

BOOST_AUTO_TEST_CASE(read_test_3dvector)
{
  readtest(Case{"../src/tests/reference_vector3d", "Vector3D", 3});
}

BOOST_AUTO_TEST_CASE(write_test_scalar)
{
  writetest(Case{"../src/tests/reference_scalars", "Scalars", 1});
}

BOOST_AUTO_TEST_CASE(write_test_2dvector)
{
  writetest(Case{"../src/tests/reference_vector2d", "Vector2D", 2});
}

BOOST_AUTO_TEST_CASE(write_test_3dvector)
{
  writetest(Case{"../src/tests/reference_vector3d", "Vector3D", 3});
}

BOOST_AUTO_TEST_SUITE_END() //read_write_tests