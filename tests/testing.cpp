#define BOOST_TEST_MODULE ASTE
#define BOOST_TEST_DYN_LINK
#include "testing.hpp"

BOOST_AUTO_TEST_SUITE(read_write_tests)

BOOST_AUTO_TEST_CASE(read_test_scalar_w_connectivity)
{
  readtest(ReadCase{"./reference_scalars", "Scalars", 1, true});
}

BOOST_AUTO_TEST_CASE(read_test_scalar_wo_connectivity)
{
  readtest(ReadCase{"./reference_scalars", "Scalars", 1, false});
}

BOOST_AUTO_TEST_CASE(read_test_2dvector_w_connectivity)
{
  readtest(ReadCase{"./reference_vector2d", "Vector2D", 2, true});
}

BOOST_AUTO_TEST_CASE(read_test_2dvector_wo_connectivity)
{
  readtest(ReadCase{"./reference_vector2d", "Vector2D", 2, false});
}

BOOST_AUTO_TEST_CASE(read_test_3dvector_w_connectivity)
{
  readtest(ReadCase{"./reference_vector3d", "Vector3D", 3, true});
}

BOOST_AUTO_TEST_CASE(read_test_3dvector_wo_connectivity)
{
  readtest(ReadCase{"./reference_vector3d", "Vector3D", 3, false});
}

BOOST_AUTO_TEST_CASE(write_test_scalar_w_connectivity)
{
  writetest(WriteCase{"./reference_scalars", "./scalar_write", "Scalars", 1, true});
}

BOOST_AUTO_TEST_CASE(write_test_scalar_wo_connectivity)
{
  writetest(WriteCase{"./reference_scalars", "./scalar_write", "Scalars", 1, false});
}

BOOST_AUTO_TEST_CASE(write_test_2dvector_w_connectivity)
{
  writetest(WriteCase{"./reference_vector2d", "./vector2d_write", "Vector2D", 2, true});
}

BOOST_AUTO_TEST_CASE(write_test_2dvector_wo_connectivity)
{
  writetest(WriteCase{"./reference_vector2d", "./vector2d_write", "Vector2D", 2, false});
}

BOOST_AUTO_TEST_CASE(write_test_3dvector_w_connectivity)
{
  writetest(WriteCase{"./reference_vector3d", "./vector3d_write", "Vector3D", 3, true});
}

BOOST_AUTO_TEST_CASE(write_test_3dvector_wo_connectivity)
{
  writetest(WriteCase{"./reference_vector3d", "./vector3d_write", "Vector3D", 3, false});
}

BOOST_AUTO_TEST_SUITE_END() // read_write_tests