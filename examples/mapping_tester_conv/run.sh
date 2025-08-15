#!/usr/bin/env bash
set -e -x

cd "$(dirname "$0")"

# The mapping-tester location
MAPPING_TESTER=../../tools/mapping-tester

# The case directory
TEST_CASE_LOCATION=case

# Generate the run scripts
python3 "${MAPPING_TESTER}/generate.py" --setup setup-test.json --outdir "${TEST_CASE_LOCATION}" --template "${MAPPING_TESTER}/config-template.xml" --exit
# Prepare the meshes
python3 "${MAPPING_TESTER}/preparemeshes.py" --setup setup-test.json --outdir "${TEST_CASE_LOCATION}" --force

export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""

# Run the actual cases
( cd "${TEST_CASE_LOCATION}" && bash ./runall.sh && bash ./postprocessall.sh )

# Gather the generated statistics
python3 "${MAPPING_TESTER}/gatherstats.py" --outdir "${TEST_CASE_LOCATION}" --file test-statistics.csv

python3 "${MAPPING_TESTER}/plotconv.py" -f test-statistics.csv

python3 "${MAPPING_TESTER}/compare.py" reference-statistics.csv test-statistics.csv
