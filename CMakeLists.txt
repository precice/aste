cmake_minimum_required (VERSION 3.1)

project(ASTE)

list (APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")

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

find_package(Boost 1.65.1 REQUIRED COMPONENTS log log_setup system program_options filesystem unit_test_framework)

option(ASTE_USE_VTK_COMPONENTS "Find VTK with components" OFF)
if(ASTE_USE_VTK_COMPONENTS)
  # This is broken on ubuntu 20.04
  find_package(VTK REQUIRED COMPONENTS CommonCore CommonDataModel IOXML IOLegacy)
else()
  # This is broken on arch
  find_package(VTK REQUIRED)
endif()
message (STATUS "VTK_VERSION: ${VTK_VERSION}")

find_package(METIS)
if (METIS_FOUND)
    add_library(metisAPI SHARED src/metisAPI.cpp)
    include_directories(${METIS_INCLUDE_DIRS})
    target_link_libraries(metisAPI ${METIS_LIBRARIES})
    target_include_directories(metisAPI PRIVATE ${METIS_INCLUDE_DIR})
endif()

find_package(MPI REQUIRED)

option(ASTE_USE_ASTE_JOINER_CPP "Use C++ implementation of precice-aste-join" OFF)

add_executable(precice-aste-run src/precice-aste-run.cpp src/common.cpp src/mesh.cpp src/configreader.cpp src/modes.cpp src/utilities.cpp src/logger.cpp)
target_include_directories(precice-aste-run PRIVATE src thirdparty)
target_link_libraries(precice-aste-run
  precice::precice
  Threads::Threads
  MPI::MPI_CXX
  ${Boost_LIBRARIES}
  ${VTK_LIBRARIES}
)

if(ASTE_SET_MESH_BLOCK)
  target_compile_definitions(precice-aste-run PRIVATE ASTE_SET_MESH_BLOCK)
endif()

if(METIS_FOUND)
  target_link_libraries(precice-aste-run metisAPI)
endif()

if(ASTE_USE_ASTE_JOINER_CPP)
add_executable(precice-aste-join src/precice-aste-join.cpp)
target_include_directories(precice-aste-join PRIVATE src thirdparty)
target_link_libraries(precice-aste-join
  ${Boost_LIBRARIES}
  ${VTK_LIBRARIES}
)
endif()

add_executable(testing tests/testing.cpp tests/read_test.cpp tests/write_test.cpp src/mesh.cpp src/logger.cpp)
target_include_directories(testing PRIVATE src thirdparty)
target_link_libraries(testing
  ${Boost_LIBRARIES}
  MPI::MPI_CXX
  ${VTK_LIBRARIES}
)

if (VTK_VERSION VERSION_LESS "8.90.0")
  # old system
  include(${VTK_USE_FILE})
else ()
  # vtk_module_autoinit is needed
  vtk_module_autoinit(
    TARGETS precice-aste-run testing precice-aste-join
    MODULES ${VTK_LIBRARIES}
    )
endif()

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-partition      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
if(NOT ASTE_USE_ASTE_JOINER_CPP)
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-join           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
endif()
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-evaluate      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

include(GNUInstallDirs)
install(TARGETS precice-aste-run DESTINATION ${CMAKE_INSTALL_BINDIR})
if(METIS_FOUND)
install(TARGETS metisAPI DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()
if(ASTE_USE_ASTE_JOINER_CPP)
install(TARGETS precice-aste-join DESTINATION ${CMAKE_INSTALL_BINDIR})
install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-partition ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-evaluate DESTINATION ${CMAKE_INSTALL_BINDIR})
else()
install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-partition ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-join ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-evaluate DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

enable_testing()

add_test(NAME read_write_test  COMMAND testing WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/tests")

# Detect and register examples as tests

set(_examples lci_2d lci_3d nn nng_scalar nng_vector mapping_tester replay_mode)

foreach(example IN LISTS _examples)
  add_test(NAME aste.example.${example}.setup
    COMMAND clean.sh
    FIXTURE_SETUP ${example})

  add_test(NAME aste.example.${example}
    COMMAND run.sh
    FIXTURE_REQUIRES ${example})

  set_tests_properties(aste.example.${example} aste.example.${example}.setup
    PROPERTIES
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/examples/${example}"
    ENVIRONMENT "PATH=$ENV{PATH}:${CMAKE_BINARY_DIR}"
    LABELS example
    RUN_SERIAL ON)
endforeach()
