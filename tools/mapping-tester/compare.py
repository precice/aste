#!/usr/bin/env python3

import argparse
from sys import exit

import polars as pl
from polars.testing import assert_frame_equal, assert_series_equal

parser = argparse.ArgumentParser()
parser.add_argument("reference")
parser.add_argument("current")
args = parser.parse_args()

rtol: float = 1e-5
atol: float = 1e-8

print(
    f"Comparing results with atol={atol} and rtol={rtol}\nGiven {args.current}\nReference {args.reference}"
)

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

check_cols = set(
    [
        "count",
        "abs_min",
        "abs_max",
        "signed_min",
        "signed_max",
        "median(abs)",
        "relative-l2",
        "99th percentile(abs)",
        "95th percentile(abs)",
        "90th percentile(abs)",
    ]
)

mismatches = []
for c in ac.intersection(check_cols):

    ref, a = df_reference.get_column(c), df_a.get_column(c)

    if not ref.ne_missing(a).any():
        continue

    difference = (ref - a).abs()
    tolerance = atol + rtol * a.abs()
    within_tolerance = (difference <= tolerance) & a.is_finite() | (ref == a)

    if ref.len() != a.len():
        print(f"\nMismatch in {c}\nLengths differ")
        mismatches.append(c)
        continue

    if within_tolerance.all():
        continue

    print(f"\nMismatch in {c}")
    print(
        f"Given     {a.to_list()}\nReference {ref.to_list()}\nOK        {within_tolerance.to_list()}"
    )
    mismatches.append(c)


if mismatches:
    print("\nThe test results differ in both files")
    print(df_a.select(order + mismatches))
    exit(len(mismatches))

print("Both files are the same")
exit(0)
