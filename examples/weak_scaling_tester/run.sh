#!/usr/bin/env bash
set -e -x

# Get the test location
TEST_LOCATION="$(pwd)"
export TEST_LOCATION

# The mapping-tester location
WEAK_SCALING_TESTER="${TEST_LOCATION}"/../../tools/mapping-scaling-tester/

GENERATOR="${TEST_LOCATION}"/../../tools/mesh-generators/generate_halton_mesh.py

# The case directory
TEST_CASE_LOCATION="${TEST_LOCATION}"/case

# Generate the run scripts
python3 "${WEAK_SCALING_TESTER}"/generate_scale_test.py --setup "${TEST_LOCATION}"/setup-test.json --outdir "${TEST_CASE_LOCATION}" --template "${WEAK_SCALING_TESTER}"/config-template.xml

# Prepare the meshes
python3 "${WEAK_SCALING_TESTER}"/prepare-scale-meshes.py --setup "${TEST_LOCATION}"/setup-test.json --outdir "${TEST_CASE_LOCATION}" --force -g "${GENERATOR}"
export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""

# Run the actual cases
cd "${TEST_CASE_LOCATION}" && bash ./runall.sh

# Postprocess the test cases
bash ./postprocessall.sh

cd "${TEST_LOCATION}"

# Gather the generated statistics
python3 "${WEAK_SCALING_TESTER}"/gatherstats.py --outdir "${TEST_CASE_LOCATION}" --file test-statistics.csv
