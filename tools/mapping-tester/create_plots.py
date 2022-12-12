#! /usr/bin/env python3

import argparse
import math
import matplotlib.pyplot as plt
import pandas
import sys


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


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))


def plot_convergence(ax, df, yname):
    xmin = df["mesh A"].min()
    xmax = df["mesh A"].max()
    ymin = df[yname].min()
    ymax = df[yname].max()

    # 1st order line
    fox = [xmax, xmin]
    foy1 = ymax
    foy2 = foy1 * (fox[1] / fox[0])
    foy = [foy1, foy2]
    ax.axline((fox[0], foy[0]), (fox[1], foy[1]), color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate("1st order", xy=(lavg(fox), lavg(foy)), color="gray", zorder=-1)

    # 2nd order line
    sox = [xmin, xmax]
    soy1 = ymin
    soy2 = soy1 * ((sox[1] / sox[0]) ** 2)
    soy = [soy1, soy2]
    print(sox, soy)
    ax.axline((sox[0], soy[0]), (sox[1], soy[1]), color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate("2nd order", xy=(lavg(sox), lavg(soy)), color="gray", zorder=-1)


def plot_error(df, prefix):
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

    plot_convergence(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-error.pdf")


def plot_memory_usage(df, prefix):
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
    ax.set_ylabel("peak memory of participant B [bytes]")

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-peakMemB.pdf")


def plot_compute_mapping_time(df, prefix):
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
    ax.set_ylabel("time to compute mapping [ms]")

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-computet.pdf")


def plot_map_data_time(df, prefix):
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
    ax.set_ylabel("time to map Data [ms]")

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-mapt.pdf")


def main(argv):
    args = parse_arguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    to_meshes = df["mesh B"].unique()
    assert len(to_meshes) == 1, f"There are {len(to_meshes)} to-meshes but only 1 is allowed. Fix your dataset!"
    df.sort_values("mesh A", inplace=True)
    plot_error(df, args.prefix)
    plot_memory_usage(df, args.prefix)
    plot_map_data_time(df, args.prefix)
    plot_compute_mapping_time(df, args.prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
