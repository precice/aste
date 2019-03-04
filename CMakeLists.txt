cmake_minimum_required (VERSION 3.1)

list (APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake-modules")

set (CMAKE_CXX_STANDARD 11)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
message(STATUS "Build configuration: " ${CMAKE_BUILD_TYPE})

find_library(precice precice PATHS $ENV{PRECICE_ROOT}/build $ENV{PRECICE_ROOT}/build/last)
if(NOT precice)
  message(FATAL_ERROR "preCICE was not found")
endif()
include_directories($ENV{PRECICE_ROOT}/src)

find_package(Boost 1.60.0 REQUIRED COMPONENTS system program_options filesystem)

find_package(METIS REQUIRED)

find_package(MPI REQUIRED)

include_directories("src")

add_library(metisAPI SHARED src/metisAPI.cpp)
target_link_libraries(metisAPI ${METIS_LIBRARIES})

add_executable(preciceMap src/preciceMap.cpp src/common.cpp)
target_include_directories(preciceMap PRIVATE ${Boost_INCLUDE_DIRS})
target_link_libraries(preciceMap ${Boost_LIBRARIES})
target_include_directories(preciceMap PRIVATE ${MPI_INCLUDE_PATH})
target_link_libraries(preciceMap ${MPI_LIBRARIES})
target_link_libraries(preciceMap ${precice})


file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/make_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/visualize_partition.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/partition_mesh.py      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/join_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/eval_mesh.py           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh_io.py             DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/mesh.py                DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
