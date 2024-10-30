#!/usr/bin/env bash
set -e -x

# Get the test location
TEST_LOCATION="$(pwd)"
export TEST_LOCATION

# The mapping-tester location
MAPPING_TESTER="${TEST_LOCATION}"/../../tools/mapping-tester/

# The case directory
TEST_CASE_LOCATION="${TEST_LOCATION}"/case

# Generate the run scripts
python3 "${MAPPING_TESTER}"/generate.py --setup "${TEST_LOCATION}"/setup-test.json --outdir "${TEST_CASE_LOCATION}" --template "${MAPPING_TESTER}"/config-template.xml --exit

# Prepare the meshes
python3 "${MAPPING_TESTER}"/preparemeshes.py --setup "${TEST_LOCATION}"/setup-test.json --outdir "${TEST_CASE_LOCATION}" --force

export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""

# Run the actual cases
cd "${TEST_CASE_LOCATION}" && bash ./runall.sh

cd "${TEST_LOCATION}"

# Gather the generated statistics
python3 "${MAPPING_TESTER}"/gatherstats.py --outdir "${TEST_CASE_LOCATION}" --file test-statistics.csv
