#! /usr/bin/env python3

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas


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


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))


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


def plotConv(ax, df, yname):
    xmin = df["mesh A"].min()
    xmax = df["mesh A"].max()
    ymin = df[yname].min()
    ymax = df[yname].max()

    print(xmin, xmax)
    print(ymin, ymax)


def plotError(df, prefix):
    yname = "relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )
    ax.set_xlabel("edge length(h) of mesh A")
    ax.set_ylabel("relative-l2 error mapping to mesh B")

    plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-error.pdf")


def plotMemory(df, prefix):
    yname = "peakMemB"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )
    ax.set_xlabel("edge length(h) of mesh A")
    ax.set_ylabel("peak memory of participant B [Kbytes]")

    # plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-peakMemB.pdf")


def plotComputeMappingTime(df, prefix):
    yname = "computeMappingTime"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )

    ax.set_xlabel("edge length(h) of mesh A")
    ax.set_ylabel("time to compute mapping [us]")

    # plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-computet.pdf")


def plotMapDataTime(df, prefix):
    yname = "mapDataTime"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )

    ax.set_xlabel("edge length(h) of mesh A")
    ax.set_ylabel("time to map Data [us]")

    # plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-mapt.pdf")


def main(argv):
    args = parseArguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    toMeshes = df["mesh B"].unique()
    assert (
        len(toMeshes) == 1
    ), f"There are {len(toMeshes)} to-meshes but only 1 is allowed. Fix your dataset!"
    df.sort_values("mesh A", inplace=True)
    plotError(df, args.prefix)
    plotMemory(df, args.prefix)
    plotMapDataTime(df, args.prefix)
    plotComputeMappingTime(df, args.prefix)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
