#!/bin/sh
set -e -u

error_exit(){
    echo "Error while running case ${array[1]}"
    exit 1
}

set -e -u

echo "- Running all examples cases..."
testcases=$(find . -maxdepth 2 -mindepth 2 -name run.sh)
numberofcases=$(echo $testcases | wc -w)
echo "- There are $numberofcases case(s) found..."

for testcase in $testcases; do
    IFS='/' read -ra array <<< "$testcase"
    cd ${array[1]}
    echo "- Running test case ${array[1]}..."
    ./run.sh || error_exit && cd -
done
