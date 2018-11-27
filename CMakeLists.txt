cmake_minimum_required (VERSION 3.1)
project(ASTE)

set (CMAKE_CXX_STANDARD 11)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
message(STATUS "Build configuration: " ${CMAKE_BUILD_TYPE})

find_library(precice precice PATHS $ENV{PRECICE_ROOT}/build/last)
if(NOT precice)
  message(FATAL_ERROR "preCICE was not found")
endif()
include_directories($ENV{PRECICE_ROOT}/src)


find_package(Boost 1.60.0 REQUIRED COMPONENTS system program_options filesystem)
include_directories(${Boost_INCLUDE_DIRS})
link_directories(${Boost_LIBRARY_DIRS})

find_package(MPI REQUIRED)
include_directories(${MPI_INCLUDE_PATH})
set(COMPILE_FLAGS  ${COMPILE_FLAGS} ${MPI_COMPILE_FLAGS})
set(LINK_FLAGS ${LINK_FLAGS} ${MPI_LINK_FLAGS})

add_executable(readMesh readMesh.cpp)
add_executable(aste aste.cpp)


target_link_libraries(aste ${Boost_LIBRARIES})
target_link_libraries(aste ${MPI_LIBRARIES})
target_link_libraries(aste ${precice})

target_link_libraries(readMesh ${Boost_LIBRARIES})
target_link_libraries(readMesh ${MPI_LIBRARIES})
target_link_libraries(readMesh ${precice})

