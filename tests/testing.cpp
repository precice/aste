#define BOOST_TEST_MODULE ASTE
#define BOOST_TEST_DYN_LINK
#include "testing.hpp"

BOOST_AUTO_TEST_SUITE(read_write_tests)

BOOST_AUTO_TEST_CASE(read_test_scalar)
{
  readtest(ReadCase{"./reference_scalars", "Scalars", 1});
}

BOOST_AUTO_TEST_CASE(read_test_2dvector)
{
  readtest(ReadCase{"./reference_vector2d", "Vector2D", 2});
}

BOOST_AUTO_TEST_CASE(read_test_3dvector)
{
  readtest(ReadCase{"./reference_vector3d", "Vector3D", 3});
}

BOOST_AUTO_TEST_CASE(write_test_scalar)
{
  writetest(WriteCase{"./reference_scalars", "./scalar_write", "Scalars", 1});
}

BOOST_AUTO_TEST_CASE(write_test_2dvector)
{
  writetest(WriteCase{"./reference_vector2d", "./vector2d_write", "Vector2D", 2});
}

BOOST_AUTO_TEST_CASE(write_test_3dvector)
{
  writetest(WriteCase{"./reference_vector3d", "./vector3d_write", "Vector3D", 3});
}

BOOST_AUTO_TEST_SUITE_END() //read_write_tests