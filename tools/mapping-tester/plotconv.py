#! /usr/bin/env python3

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np
import polars as pl


def parseArguments(args):
    parser = argparse.ArgumentParser(
        description="Creates convergence plots from gathered stats"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        default="stats.csv",
        help="The CSV file containing the gathered stats.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="result",
        help="The prefix for all generated PDF plots.",
    )
    return parser.parse_args(args)


# seaborn.color_palette("colorblind", 10).as_hex()
style_colours = [
    "#0173b2",
    "#de8f05",
    "#029e73",
    "#d55e00",
    "#cc78bc",
    "#ca9161",
    "#fbafe4",
    "#949494",
    "#ece133",
    "#56b4e9",
]
style_markers = ["o", "D", "s"]
styles = [(c, m) for m in style_markers for c in style_colours]


def plotBack(
    df: pl.DataFrame, yname: str, ylabel: str, xname: str, xlabel: str, filename: str
):
    if xname not in df.columns:
        print(f"Skipping {xname}-{yname} plot as {xname} not found in dataset.")
        return

    if yname not in df.columns:
        print(f"Skipping {xname}-{yname} plot as {yname} not found in dataset.")
        return

    fig, ax = plt.subplots(sharex=True, sharey=True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if df[xname].dtype.is_numeric():
        ax.set_xscale("log")

    if df[yname].dtype.is_numeric():
        ax.set_yscale("log")

    series = list(df.group_by("mapping"))
    series.sort(key=lambda x: x[0])

    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        ax.plot(
            group[xname],
            group[yname],
            label=name,
            marker=marker,
            color=color,
        )

    plt.gca().invert_xaxis()
    plt.grid()
    plt.legend()
    plt.savefig(filename + ".pdf")


def plotVariable(df: pl.DataFrame, yname: str, ylabel: str, filename: str):
    plotBack(
        df,
        yname=yname,
        ylabel=ylabel,
        xname="mesh A",
        xlabel="edge length(h) of mesh A",
        filename=filename,
    )


def plotRuntimeAccuracy(df: pl.DataFrame, yname: str, ylabel: str, filename: str):
    plotBack(
        df,
        yname=yname,
        ylabel=ylabel,
        xname="relative-l2",
        xlabel="relative l2-error",
        filename=filename,
    )


def main(argv):
    args = parseArguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pl.read_csv(args.file).sort("mesh A")
    toMeshes = df["mesh B"].unique()
    assert (
        len(toMeshes) == 1
    ), f"There are {len(toMeshes)} to-meshes but only 1 is allowed. Fix your dataset!"

    if not df["mesh A"].dtype.is_numeric():
        print("Note: 'mesh A' isn't numeric. The x-axis will not use log scaling.")

    plotVariable(
        df,
        yname="relative-l2",
        ylabel="relative-l2 error mapping to mesh B",
        filename=f"{args.prefix}-error",
    )
    plotVariable(
        df,
        yname="peakMemB",
        ylabel="peak memory of participant B [Kbytes]",
        filename=f"{args.prefix}-peakMemB",
    )
    plotVariable(
        df,
        yname="computeMappingTime",
        ylabel="time to compute mapping [us]",
        filename=f"{args.prefix}-computet",
    )
    plotVariable(
        df,
        yname="mapDataTime",
        ylabel="time to map Data [us]",
        filename=f"{args.prefix}-mapt",
    )
    plotRuntimeAccuracy(
        df,
        yname="computeMappingTime",
        ylabel="time to compute mapping [us]",
        filename=f"{args.prefix}-computetAccuracy",
    )
    plotRuntimeAccuracy(
        df,
        yname="mapDataTime",
        ylabel="time to map Data [us]",
        filename=f"{args.prefix}-maptAccuracy",
    )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
