cmake_minimum_required (VERSION 3.22)

project(ASTE VERSION 3.3.0)

message(STATUS "ASTE version: ${ASTE_VERSION_MAJOR}.${ASTE_VERSION_MINOR}.${ASTE_VERSION_PATCH}")
list (APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")

set (CMAKE_CXX_STANDARD 17)
set (CMAKE_CXX_STANDARD_REQUIRED YES)
set (CMAKE_CXX_EXTENSIONS NO)
set (CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(POLICY CMP0167)
  cmake_policy(SET CMP0167 NEW)
endif()

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
message(STATUS "Build configuration: " ${CMAKE_BUILD_TYPE})

option(ASTE_SET_MESH_BLOCK "Use block versions to set mesh primitives." ON)

find_package (Threads REQUIRED)

find_package(precice 3.0 REQUIRED)

find_package(Boost 1.71.0 CONFIG REQUIRED COMPONENTS log log_setup system program_options unit_test_framework)

# Initial attempt to find VTK without specifying components (only supported for VTK9)
find_package(VTK QUIET)

if(VTK_FOUND AND NOT "${VTK_VERSION}" VERSION_LESS "9.0")
    # Attempt to find VTK with required components for VTK 9+
    find_package(VTK 9.0 REQUIRED COMPONENTS CommonCore CommonDataModel IOXML IOLegacy CONFIG QUIET)
endif()

if(NOT VTK_FOUND)
    message(FATAL_ERROR "Unable to locate a suitable version of VTK. Please check your VTK installation.")
else()
    message(STATUS "Using VTK version ${VTK_VERSION} from ${VTK_DIR}")
endif()

find_package(METIS)
if (METIS_FOUND)
    add_library(metisAPI SHARED src/metisAPI.cpp)
    include_directories(${METIS_INCLUDE_DIRS})
    target_link_libraries(metisAPI ${METIS_LIBRARIES})
    target_include_directories(metisAPI PRIVATE ${METIS_INCLUDE_DIR})
endif()

find_package(MPI REQUIRED)

add_executable(precice-aste-run src/precice-aste-run.cpp src/common.cpp src/mesh.cpp src/configreader.cpp src/modes.cpp src/utilities.cpp src/logger.cpp)
target_include_directories(precice-aste-run PRIVATE src thirdparty)
target_link_libraries(precice-aste-run
  precice::precice
  Threads::Threads
  Boost::boost
  Boost::log
  Boost::log_setup
  Boost::program_options
  Boost::system
  Boost::thread
  Boost::unit_test_framework
  MPI::MPI_CXX
  ${VTK_LIBRARIES}
)

if(ASTE_SET_MESH_BLOCK)
  target_compile_definitions(precice-aste-run PRIVATE ASTE_SET_MESH_BLOCK)
endif()

if(METIS_FOUND)
  target_link_libraries(precice-aste-run metisAPI)
endif()


add_executable(test-precice-aste tests/testing.cpp tests/read_test.cpp tests/write_test.cpp src/mesh.cpp src/logger.cpp)
target_include_directories(test-precice-aste PRIVATE src thirdparty)
target_link_libraries(test-precice-aste
  Boost::boost
  Boost::log
  Boost::log_setup
  Boost::program_options
  Boost::system
  Boost::thread
  Boost::unit_test_framework
  MPI::MPI_CXX
  ${VTK_LIBRARIES}
)

if (VTK_VERSION VERSION_LESS "9.0")
  # old system
  include(${VTK_USE_FILE})
else ()
  # vtk_module_autoinit is needed
  vtk_module_autoinit(
    TARGETS precice-aste-run test-precice-aste
    MODULES ${VTK_LIBRARIES}
    )
endif()

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-partition      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-join           DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-evaluate      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

include(GNUInstallDirs)
install(TARGETS precice-aste-run DESTINATION ${CMAKE_INSTALL_BINDIR})
if(METIS_FOUND)
install(TARGETS metisAPI DESTINATION ${CMAKE_INSTALL_LIBDIR})
endif()
install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-partition ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-join ${CMAKE_CURRENT_SOURCE_DIR}/src/precice-aste-evaluate DESTINATION ${CMAKE_INSTALL_BINDIR})

enable_testing()

add_test(NAME read_write_test  COMMAND test-precice-aste WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/tests")

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
    ENVIRONMENT_MODIFICATION "PATH=path_list_append:${CMAKE_BINARY_DIR}"
    LABELS example
    RUN_SERIAL ON)
endforeach()
