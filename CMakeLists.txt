cmake_minimum_required (VERSION 3.1)

project(ASTE)


list (APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake-modules")

set (CMAKE_CXX_STANDARD 14)
set (CMAKE_CXX_STANDARD_REQUIRED YES)
set (CMAKE_CXX_EXTENSIONS NO)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
message(STATUS "Build configuration: " ${CMAKE_BUILD_TYPE})

option(ASTE_SET_MESH_BLOCK "Use block versions to set mesh primitives." ON)

find_package (Threads REQUIRED)

find_package(precice REQUIRED CONFIG)

find_package(Boost 1.65.1 REQUIRED COMPONENTS system program_options filesystem unit_test_framework)

find_package(VTK REQUIRED)
if (VTK_FOUND)
  if(${VTK_VERSION} LESS 7.1.1)
    message(WARNING "The detected VTK version has not been tested and might have compatibility issues.")
  endif()
endif()
include(${VTK_USE_FILE})

find_package(METIS)
if (METIS_FOUND)
    add_library(metisAPI SHARED src/metisAPI.cpp)
    target_link_libraries(metisAPI ${METIS_LIBRARIES})
endif()

find_package(MPI REQUIRED)

add_executable(preciceMap src/preciceMap.cpp src/common.cpp src/easylogging++.cc src/mesh.cpp)
target_include_directories(preciceMap PRIVATE src)
target_link_libraries(preciceMap
  precice::precice
  Threads::Threads
  Boost::boost
  Boost::filesystem
  Boost::program_options
  Boost::system
  MPI::MPI_CXX
  ${VTK_LIBRARIES}
)

if(ASTE_SET_MESH_BLOCK)
  target_compile_definitions(preciceMap PRIVATE ASTE_SET_MESH_BLOCK)
endif()

if(METIS_FOUND)
  target_link_libraries(preciceMap metisAPI)
endif()

add_executable(write_test src/tests/write_test.cpp src/mesh.cpp)
target_include_directories(write_test PRIVATE src)
target_link_libraries(write_test
  Boost::filesystem
  Boost::boost
  Boost::unit_test_framework
  ${VTK_LIBRARIES}
)

add_executable(read_test src/tests/read_test.cpp src/mesh.cpp)
target_include_directories(read_test PRIVATE src)
target_link_libraries(read_test
  Boost::filesystem
  Boost::boost
  Boost::unit_test_framework
   ${VTK_LIBRARIES}
)

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/make_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/visualize_partition.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/partition_mesh.py      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/join_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/eval_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/vtk_calculator.py      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh_io.py             DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh.py                DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

enable_testing()

add_test(write_scalar write_test scalar)
add_test(check_scalar md5sum -c ${CMAKE_CURRENT_SOURCE_DIR}/src/tests/scalarmd5)
set_tests_properties (check_scalar PROPERTIES PASS_REGULAR_EXPRESSION "OK")

add_test(write_vector2d write_test vector2d)
add_test(check_vector2d md5sum -c ${CMAKE_CURRENT_SOURCE_DIR}/src/tests/vector2dmd5)
set_tests_properties (check_vector2d PROPERTIES PASS_REGULAR_EXPRESSION "OK")

add_test(write_vector3d write_test vector3d)
add_test(check_vector3d md5sum -c ${CMAKE_CURRENT_SOURCE_DIR}/src/tests/vector3dmd5)
set_tests_properties (check_vector3d PROPERTIES PASS_REGULAR_EXPRESSION "OK")
