#!/usr/bin/env python3

import argparse
import pathlib

import numpy as np
import polars as pl


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Aggregates statistics of multiple runs. See mapping-tester repreat.py"
    )
    parser.add_argument(
        "file",
        type=pathlib.Path,
        help="Statistics file to aggregate runs on",
    )
    parser.add_argument(
        "kind",
        choices=["mean", "median", "variance"],
        help="Kind of aggregation",
    )
    parser.add_argument(
        "-x",
        "--exclude-min-max",
        dest="exclude",
        action="store_true",
        help="Remove min and max from the data set before aggregating.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="aggregated.csv",
        type=pathlib.Path,
        help="Statistics file write the aggregated results to.",
    )
    return parser.parse_args()


def trim(series: pl.Series):
    return series.sort()[1:-1]


def run(file: pathlib.Path, kind: str, exclude: bool, dest: pathlib.Path):

    df = pl.read_csv(file).drop("run")

    # returns a lambda that creates a pl.Exception for a given column name
    func = {
        "median": lambda c: pl.col(c).median(),
        "mean": lambda c: (
            pl.col(c).map_batches(trim, return_dtype=pl.self_dtype()).mean()
            if exclude
            else pl.col(c).mean()
        ),
        "variance": lambda c: (
            pl.col(c).map_batches(trim, return_dtype=pl.self_dtype()).var()
            if exclude
            else pl.col(c).var()
        ),
    }[kind]

    case = ["mapping", "constraint", "mesh A", "mesh B", "ranks A", "ranks B"]
    df = df.group_by(case).agg([func(c) for c in df.columns if c not in case])

    print(f"Writing output to {dest}")
    df.write_csv(dest)


def main():
    args = parseArguments()
    assert args.file.exists()
    run(args.file, args.kind, args.exclude, args.output)


if __name__ == "__main__":
    main()
