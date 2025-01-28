#!/usr/bin/env bash
set -e -x

cd "$(basedir "$0")"

# The mapping-tester location
MAPPING_TESTER=../../tools/mapping-tester

# Generate the run scripts
python3 "${MAPPING_TESTER}/generate.py" --template "${MAPPING_TESTER}"/config-template.xml --exit

# Prepare the meshes
python3 "${MAPPING_TESTER}/preparemeshes.py" --force

export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""

# Run the actual cases
bash cases/runall.sh

# Postprocess the test cases
bash cases/postprocessall.sh

# Gather the generated statistics
python3 "${MAPPING_TESTER}/gatherstats.py" --file test-statistics.csv

python3 "${MAPPING_TESTER}/compare.py" reference-statistics.csv test-statistics.csv
