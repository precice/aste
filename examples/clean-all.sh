#!/bin/sh
set -e -u

cd "$(dirname "$0")"

echo "- Cleaning up all test examples..."

find . -maxdepth 2 -mindepth 2 -name clean.sh -execdir sh -c './clean.sh' \;
