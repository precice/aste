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


# 2.4.0 has a bug so it requires something greater than 2.4.0 for NN
# Also, tetrahedra appeared after 2.4.0
IF(${precice_VERSION} VERSION_GREATER "2.4.0")
  SET(SUPPORT_NN_GRADIENT_MAPPING_AND_TETRA ON)
ELSE()
  SET(SUPPORT_NN_GRADIENT_MAPPING_AND_TETRA OFF)
ENDIF()

option(ASTE_NN_GRADIENT_MAPPING_AND_TETRA "Support nearest neighbour gradient mapping." ${SUPPORT_NN_GRADIENT_MAPPING_AND_TETRA})

MESSAGE(STATUS "Support for nearest-neighbor-gradient mapping and tetrahedra: ${ASTE_NN_GRADIENT_MAPPING_AND_TETRA}")

find_package(Boost 1.65.1 REQUIRED COMPONENTS log log_setup system program_options filesystem unit_test_framework)

find_package(VTK REQUIRED)
message (STATUS "VTK_VERSION: ${VTK_VERSION}")

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
  MPI::MPI_CXX
  ${Boost_LIBRARIES}
  ${VTK_LIBRARIES}
)

if(ASTE_SET_MESH_BLOCK)
  target_compile_definitions(precice-aste-run PRIVATE ASTE_SET_MESH_BLOCK)
endif()

if(ASTE_NN_GRADIENT_MAPPING_AND_TETRA)
  target_compile_definitions(precice-aste-run PRIVATE ASTE_NN_GRADIENT_MAPPING_AND_TETRA)
endif()

if(METIS_FOUND)
  target_link_libraries(precice-aste-run metisAPI)
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
    TARGETS precice-aste-run testing
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

add_test(NAME read_write_test  COMMAND testing WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/tests")
