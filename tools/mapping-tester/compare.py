#!/usr/bin/env python3

import argparse
from sys import exit

import polars as pl
from polars.testing import assert_frame_equal

parser = argparse.ArgumentParser()
parser.add_argument("reference")
parser.add_argument("current")
args = parser.parse_args()

df_a = pl.read_csv(args.current)
df_reference = pl.read_csv(args.reference)

ac = set(df_a.columns)
rc = set(df_reference.columns)
if ac != rc:
    print(f"Columns don't match!")
    print(f"Missing:    {' '.join(rc - ac)}")
    print(f"Unexpected: {' '.join(ac - rc)}")
    exit(1)

# columns defining test case
order = ["mesh A", "mesh B", "mapping", "constraint", "ranks A", "ranks B"]
missing = set(order) - ac
if missing:
    print(f"Columns are missing from test setup: {' '.join(missing)}")
    exit(1)

# Ensure the case order is identical
df_a = df_a.sort(order)
df_reference = df_reference.sort(order)

# Test if the setups are identical
try:
    assert_frame_equal(df_a.select(order), df_reference.select(order))
except AssertionError as e:
    print("The test setup differs in both files")
    print(e)
    exit(1)

# Time and memory columns if they are valid
posCols = {c for c in ac for m in ["time", "mem"] if m in c.lower()}
for pc in posCols:
    if not (df_a.select(pc).to_numpy() > 0.0).all():
        print(f"Column {pc} contains values <= 0")
        exit(1)

# Test data columns if they approximately the same
try:
    assert_frame_equal(df_a.drop(posCols), df_reference.drop(posCols))
except AssertionError as e:
    print("The test results differ in both files")
    print(e)
    exit(1)

print("Both files are the same")
exit(0)
