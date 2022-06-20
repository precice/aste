#!/bin/sh
set -e -u

echo "- Running all examples cases..."

find . -maxdepth 2 -mindepth 2 -name run.sh -execdir sh -c './run.sh' \;
