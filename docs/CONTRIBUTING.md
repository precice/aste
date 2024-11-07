# Contributing to ASTE

**Thank you for considering contributing to our project! We welcome contributions of all kinds.**

The documentation of ASTE is rendered on [the preCICE website](https://precice.org/tooling-aste.html) and hosted in this repository under `./docs/README.md`.

## Reporting Bugs

- Ensure the bug is not already reported by searching [in our GitHub issues](https://github.com/precice/aste/issues).
- Use a clear and descriptive title.
- Provide details on how to reproduce the specific bug.

## Submitting Pull Requests

See the [contribute to preCICE page](https://precice.org/community-contribute-to-precice.html) for general guidelines.

### Testing

ASTE uses [`CMake`](https://cmake.org/) as build system. Code changes can be tested using the command `ctest`, which is also run by a GitHub Action workflow. It executes unit tests located in `./tests/` and integration tests located in `./examples/`. Add tests for new features in your pull request. For unit tests, have a look at `./tests/read_test.cpp` as an example. To add an integration test, add a new directory in `./examples/<feature>` and include a `run.sh` script and a `clean.sh` script. For an integration test example, have a look at `./examples/nn`.

### Changelog

We curate a `CHANGELOG.md` file, which tracks notable changes of this project across releases. Add a changelog entry when contributing. However, instead of directly editing `CHANGELOG.md`, please add a file `123.md` in `changelog-entries`, where `123` is your pull request number. This helps reducing merge conflicts. We collect these files before releasing.

### Code formatting

Similar to [preCICE](https://precice.org/dev-docs-dev-tooling.html#setting-up-pre-commit), we use pre-commit to ensure consistent formatting of source code and documentation files. Under the hood, pre-commit uses clang-format and black as formatters. Install [pre-commit](https://pre-commit.com/) and then call `pre-commit install` at the root of this repository to setup the automation.

## Contact

For questions, reach out through the [preCICE community channels](https://precice.org/community-channels.html).
