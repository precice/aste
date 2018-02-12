cmake_minimum_required (VERSION 3.0)
project(ASTE)

set (CMAKE_CXX_STANDARD 11)

add_executable(readMesh readMesh.cpp)
add_executable(aste main.cpp)

# set(CMAKE_CXX_STANDARD 11)

find_library(precice precice PATHS $ENV{PRECICE_ROOT}/build/last)
if(NOT precice)
  message(FATAL_ERROR "preCICE was not found")
endif()
include_directories($ENV{PRECICE_ROOT}/src)
target_link_libraries(readMesh ${precice})
target_link_libraries(aste ${precice})
# set(CMAKE_LIBRARY_PATH ${CMAKE_LIBRARY_PATH} $ENV{PRECICE_ROOT}/build/last)

find_package(Boost 1.60.0 REQUIRED
  COMPONENTS system program_options filesystem)  

find_package(MPI REQUIRED)
include_directories(${MPI_INCLUDE_PATH})
set(COMPILE_FLAGS  ${COMPILE_FLAGS} ${MPI_COMPILE_FLAGS})
set(LINK_FLAGS ${LINK_FLAGS} ${MPI_LINK_FLAGS})

target_link_libraries(readMesh ${Boost_LIBRARIES})
target_link_libraries(aste ${Boost_LIBRARIES})
target_link_libraries(readMesh ${MPI_LIBRARIES})
target_link_libraries(aste ${MPI_LIBRARIES})


# get_cmake_property(_variableNames VARIABLES)
# foreach (_variableName ${_variableNames})
    # message(STATUS "${_variableName}=${${_variableName}}")
# endforeach()
