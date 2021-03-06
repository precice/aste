cmake_minimum_required (VERSION 3.1)

project(ASTE)


list (APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake-modules")

set (CMAKE_CXX_STANDARD 11)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
message(STATUS "Build configuration: " ${CMAKE_BUILD_TYPE})

find_package (Threads REQUIRED)

find_package(precice REQUIRED CONFIG)

find_package(Boost 1.65.1 REQUIRED COMPONENTS system program_options filesystem)

find_package(METIS)
if (METIS_FOUND)
    add_library(metisAPI SHARED src/metisAPI.cpp)
    target_link_libraries(metisAPI ${METIS_LIBRARIES})
endif()

find_package(MPI REQUIRED)

add_executable(preciceMap src/preciceMap.cpp src/common.cpp src/easylogging++.cc)
target_include_directories(preciceMap PRIVATE src)
target_link_libraries(preciceMap
  precice::precice
  Threads::Threads
  Boost::boost
  Boost::filesystem
  Boost::program_options
  Boost::system
  MPI::MPI_CXX
)

if(METIS_FOUND)
  target_link_libraries(preciceMap metisAPI)
endif()

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/make_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/visualize_partition.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/partition_mesh.py      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/join_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/eval_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/vtk_calculator.py      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh_io.py             DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh.py                DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
