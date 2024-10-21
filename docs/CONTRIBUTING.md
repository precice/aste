# Contributing to ASTE

**Thank you for considering contributing to our project! We welcome contributions of all kinds.**

The documentation of this project is rendered as [part of the preCICE project](https://precice.org/tooling-aste.html) and hosted in this repository under `./docs/README.md`. The documentation should provide clear guidance on how to build and use ASTE.

## Reporting Bugs

- Ensure the bug is not already reported by searching [in our GitHub issues](https://github.com/precice/aste/issues).
- Use a clear and descriptive title.
- Provide details on how to reproduce the specific bug.

## Submitting Pull Requests

For information about a general contributing workflow, consider the information at the page [contributing to preCICE](https://precice.org/community-contribute-to-precice.html).

### Testing

As explained in the documentation, ASTE uses [`CMake`](https://cmake.org/) as build system. Applied code changes can be tested using the command `ctest` which will report any failing tests.

`ctest` executes the unit tests of the project, which are located in `./tests/` and integration tests located in `./examples/`. Please add a test for newly added features in your pull request. For unit tests, have a look at `./tests/read_test.cpp` for an exemplary test. To add an integration test, add a new directory in `./examples/<feature>` and include a `run.sh` as well as a `clean.sh` script such that the test can be incorporated into `ctest`. An exampe for an integration test might be given by `./examples/nn`.

### Changelog

We curate a `CHANGELOG.md` file which tracks notable changes of this project across releases. Please add a changelog entry when contributing. However, instead of directly editing `CHANGELOG.md`, please add a file `123.md` in `changelog-entries`, where `123` your pull request number. This helps reduce merge conflicts and we will merge these files at the time we release a new version.

### Code formatting

Similar to [preCICE](https://precice.org/dev-docs-dev-tooling.html#setting-up-pre-commit), we use [pre-commit](https://pre-commit.com/) to ensure consistent formatting of source code and documentation files. Under the hood, `pre-commit` relies on other tools such as `clang-format` and `black` to apply the correct formatting. Please install `pre-commit` and then install the hook in this repository using `pre-commit install`. This ensures correct formatting for future commits.

### Automatic checks

We check every contribution with a GitHub Action workflows which report at the bottom of each pull request.

## Contact

For questions, reach out through our [community channels](https://precice.org/community-channels.html).
