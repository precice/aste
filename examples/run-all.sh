#!/bin/bash
set -e -u

# Print the problmatic case and increase error count
detect_error(){
    echo "Error while running case ${array[1]}"
    err_count=$((err_count + 1))
}

echo "- Running all examples cases..."
test_cases=$(find . -maxdepth 2 -mindepth 2 -name run.sh)
number_of_cases=$(echo "$test_cases" | wc -w)
echo "- There are $number_of_cases case(s) found..."

# Initial directory and error count
run_all_dir=$(pwd)
err_count=0

# Run all cases
for testcase in $test_cases; do
    array=($(echo "$testcase" | tr "/" "\n"))
    cd "${array[1]}"
    echo "- Running test case ${array[1]}..."
    ./run.sh || detect_error
    cd "$run_all_dir"
done

if [  $err_count -eq 0 ]; then
    echo "All tests passed"
else
    echo "$err_count out of $number_of_cases failed"
    exit 1
fi
