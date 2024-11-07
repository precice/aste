# ASTE Change Log

All notable changes to this project will be documented in this file.

## [v3.3.0] - 2024-11-07

### Added

- Added a code of conduct from Covenant (see `CODE_OF_CONDUCT.md`). [#205](https://github.com/precice/aste/pull/205)
- Added contributing guidelines (see `docs/CONTRIBUTING.md`). [#205](https://github.com/precice/aste/pull/205)
- Added documentation to the mapping tester. [#209](https://github.com/precice/aste/pull/209)
- Added scoping support to gathering events. [#207](https://github.com/precice/aste/pull/207)
- Added macOS continuous integration support for ASTE. [#202](https://github.com/precice/aste/pull/202)
- Added a cached VTK build in ASTE CI for faster build times. [#211](https://github.com/precice/aste/pull/211)

### Changed

- Changed CMake to always find Boost using its CMake Config. [#194](https://github.com/precice/aste/pull/194)
- Highlighted ASTE's dependency on preCICE more clearly in the documentation. [#206](https://github.com/precice/aste/pull/206)
- Made `run-all` script for examples more robust. [#201](https://github.com/precice/aste/pull/201)

### Fixed

- Fixed linker errors when FindBoost uses the CMake Config. [#194](https://github.com/precice/aste/pull/194)
- Fixed SEGFAULT in `precice-aste-run` if no mesh is found for the given name. [#196](https://github.com/precice/aste/pull/196)

## [v3.2.0] - 2024-07-31

### Fixed

- Fixed CMake installation for VTK 9 and higher. [#184](https://github.com/precice/aste/pull/184)

### Changed

- Updated documentation for current VTK issues. [#185](https://github.com/precice/aste/pull/185)
- Updated CI to use manual installation of VTK. [#187](https://github.com/precice/aste/pull/187)
- Cleaned up Python requirements. [#193](https://github.com/precice/aste/pull/193)

## [v3.1.0] - 2024-03-22

### Added

- Introduced a Halton Mesh Generator for improved mesh sampling. [#155](https://github.com/precice/aste/pull/155)
- Added a unit grid generator. [#154](https://github.com/precice/aste/pull/154)
- Added connectivity to the Halton Mesh Generator using Delaunay Triangulation. [#157](https://github.com/precice/aste/pull/157)
- Set up Dependabot for dependency updates. [#164](https://github.com/precice/aste/pull/164)
- Added pre-commit hooks for website linting. [#183](https://github.com/precice/aste/pull/183)

### Changed

- Updated codebase from C++14 to C++17 standard. [#138](https://github.com/precice/aste/pull/138)
- Replaced `boost::filesystem` with `std::filesystem`. [#160](https://github.com/precice/aste/pull/160)
- Updated ASTE for compatibility with preCICE version 3. [#161](https://github.com/precice/aste/pull/161)
- Merged `initialize` and `initializeData` functions. [#158](https://github.com/precice/aste/pull/158)
- Renamed test executable from `test` to `precice-aste-test`. [#175](https://github.com/precice/aste/pull/175)
- Updated preCICE packages in continuous integration. [#167](https://github.com/precice/aste/pull/167)

### Fixed

- Improved handling of ASTE and preCICE logging. [#136](https://github.com/precice/aste/pull/136)
- Fixed wrong variable in Franke3D function. [#173](https://github.com/precice/aste/pull/173)
- Fixed vertex resolution in partitioner and joiner. [#180](https://github.com/precice/aste/pull/180)
- Changed scripts to use `env time` to bypass built-in `time`. [#178](https://github.com/precice/aste/pull/178)

### Released

- Released ASTE version compatible with preCICE v3. [#182](https://github.com/precice/aste/pull/182)

## [v3.0.0] - 2022-09-28

### Added

- Fully ported ASTE to the VTK library, eliminating custom data structures.
- Unified user interface for the main C++ core (`precice-aste-run`) and Python tools.
- Introduced replay-mode to emulate participants in coupled simulations.
- Added support for `nearest-neighbor-gradient` and `linear-cell` interpolation mappings.
- Supported processing of tetrahedral meshes and gradient data.
- Created dedicated ASTE documentation and tutorial resources.

### Changed

- Improved logging for the C++ executable and Python tools.
- Renamed executables for consistency.
- Updated VTK version requirements and improved component detection.
- Switched to pre-commit hooks for code formatting.
- Refactored codebase for better performance and maintainability.

### Fixed

- Resolved compiler warnings and code style issues.
- Fixed MPI linking issues for test executables.
- Corrected logger names and typos in documentation.
- Fixed issues with `vtk_calculator` removing `diffdata` in diff mode.

### Removed

- Removed obsolete scripts and deprecated functions.

## [v2.0.0] - 2020-02-10

### Added

- Support for preCICE v2, including migration to the single-step setup.

### Changed

- Updated configuration files to be compatible with preCICE v2.

## [v1.1.0] - 2019-11-20

### Added

- Connectivity information to mesh creation and partition tools.
- Filter for cell types in mesh handling.

### Changed

- Sped up edge generation using `boost::flat_map` for better performance.
- Modernized CMake configurations for improved build process.
- Migrated `preciceMap`, `aste`, and `visualize_partition` tools to the new system.

### Fixed

- Issues with connectivity output ensuring correct data representation.
- Build issues in CMake configuration.

### Removed

- Dependency on the `prettyprint` library to reduce external dependencies.
