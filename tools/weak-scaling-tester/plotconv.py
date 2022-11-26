#! /usr/bin/env python3

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas

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


def parse_arguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
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


def plot_memory(df, prefix):
    yname = "peakMemB"
    _, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            x="ranks A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )
    ax.set_xlabel("Ranks of participant A")
    ax.set_ylabel("peak memory of participant B [bytes]")
    plt.grid()
    plt.savefig(prefix + "-peakMemB.pdf")


def plot_compute_mapping_time(df, prefix):
    yname = "computeMappingTime"
    _, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            x="ranks A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )

    ax.set_xlabel("Ranks of participant A")
    ax.set_ylabel("time to compute mapping [ms]")
    plt.grid()
    plt.savefig(prefix + "-computet.pdf")


def plot_map_data_time(df, prefix):
    yname = "mapDataTime"
    _, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            x="ranks A",
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )

    ax.set_xlabel("Ranks of participant A")
    ax.set_ylabel("time to map Data [ms]")
    plt.grid()
    plt.savefig(prefix + "-mapt.pdf")


def main(argv):
    args = parse_arguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    df.sort_values("ranks A", inplace=True)
    plot_memory(df, args.prefix)
    plot_map_data_time(df, args.prefix)
    plot_compute_mapping_time(df, args.prefix)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
