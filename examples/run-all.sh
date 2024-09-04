#!/bin/bash
set -e -u

# Get the absolute directory of where the script is located (execution from anywhere)
script_dir=$(dirname "$(readlink -f "$0")")

# Function to handle errors
detect_error() {
    echo "Error while running case $case_dir"
    err_count=$((err_count + 1))
}

# We only look for test cases one level lower since the mapping-tester generates additional run scripts
run_test_cases() {
    local base_dir="$1"

    test_cases=$(find "$base_dir" -maxdepth 2 -mindepth 2 -name run.sh)

    # Check if there are any cases
    number_of_cases=$(echo "$test_cases" | wc -w)
    if [ "$number_of_cases" -eq 0 ]; then
        echo "No test cases found in $base_dir."
        return
    fi
    echo "- Found $number_of_cases case(s) in $base_dir..."

    for testcase in $test_cases; do
        case_dir=$(dirname "$testcase")
        echo "- Running test case in $case_dir ..."

        # Change to the test case directory
        cd "$case_dir"

        # Run the test and check for errors
        ./run.sh || detect_error

        # Return to the original directory
        cd "$base_dir"
    done
}

echo "- Running all example cases from $script_dir..."

# Initialize error count
err_count=0

# Run all test cases starting from the script's directory
run_test_cases "$script_dir"

# Report results
if [ "$err_count" -eq 0 ]; then
    echo "All tests passed"
else
    echo "$err_count test(s) failed."
    exit 1
fi
