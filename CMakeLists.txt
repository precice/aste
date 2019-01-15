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

find_library(precice precice PATHS $ENV{PRECICE_ROOT}/build)
if(NOT precice)
  message(FATAL_ERROR "preCICE was not found")
endif()
include_directories($ENV{PRECICE_ROOT}/src)

find_package(Boost 1.60.0 REQUIRED COMPONENTS system program_options filesystem)

find_package(METIS REQUIRED)

find_package(Eigen3 REQUIRED)

find_package(MPI REQUIRED)

add_executable(preciceDist preciceDist.cpp)
add_library(common common.cpp)
add_library(metisAPI SHARED metisAPI.cpp)

target_link_libraries(common ${precice})

target_link_libraries(metisAPI ${METIS_LIBRARIES})

target_link_libraries(preciceDist ${Boost_LIBRARIES})
target_include_directories(preciceDist PRIVATE ${Boost_INCLUDE_DIRS})
target_link_libraries(preciceDist ${MPI_LIBRARIES})
target_include_directories(preciceDist PRIVATE ${MPI_INCLUDE_PATH})
target_link_libraries(preciceDist ${precice})
target_link_libraries(preciceDist common)
target_include_directories(preciceDist PRIVATE ${EIGEN3_INCLUDE_DIR})


file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/partition_mesh.py
         DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/join_mesh.py
         DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/eval_mesh.py
         DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/precice.xml
         DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/demo.sh
         DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
