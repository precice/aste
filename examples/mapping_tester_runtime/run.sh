#!/usr/bin/env bash
set -e -x

cd "$(basedir "$0")"

# The mapping-tester location
export MAPPING_TESTER=../../tools/mapping-tester

# Generate the run scripts
python3 "${MAPPING_TESTER}/generate.py" --template "${MAPPING_TESTER}"/config-template.xml --exit

# Prepare the meshes
python3 "${MAPPING_TESTER}/preparemeshes.py" --force

export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""


python3 "${MAPPING_TESTER}/repeat.py" 5 --file "test-statistics{}.csv"

python3 "${MAPPING_TESTER}/compare.py" reference-statistics.csv test-statistics.csv
