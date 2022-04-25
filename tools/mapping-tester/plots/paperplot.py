#! python3


import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt
import math
import itertools


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), default="stats.csv",
                        help='The CSV file containing the gathered stats.')
    parser.add_argument('--show', action="store_true", help='Shows the plots insead of saving them.')
    return parser.parse_args(args)


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))


def getStyler():
    styles = ['solid', 'dashed', 'dashdot']
    colors = [
        '#0173b2',
        '#de8f05',
        '#029e73',
        '#d55e00',
        '#cc78bc',
        '#ca9161',
        '#fbafe4',
        '#949494',
        '#ece133',
        '#56b4e9']
    markers = ['o', 'v', '^', 'D', '*']
    for style in itertools.product(styles, markers, colors):
        yield style


def plot_order(ax, nth, xmin, xmax, ymin, ymax):
    x1, y1 = xmax, ymax

    def f(x):
        return y1 * ((x / x1)**nth)

    xl, xu = xmin, xmax
    for step in range(4):
        xt = lavg([xu, xl])
        yt = f(xt)

        if yt > ymin:
            xu = xt
        if yt < ymin:
            xl = xt
    x2, y2 = xu, f(xu)

    xs, ys = [x1, x2], [y1, y2]
    ax.plot(xs, ys, color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate(
        "{} order".format(nth),
        xy=(lavg(xs), lavg(ys)),
        color="gray",
        zorder=-1
    )


def main(argv):
    args = parseArguments(argv[1:])

    df = pandas.read_csv(args.file)
    numeric_cols = [
        'mesh A',
        'mesh B',
        'count',
        'min',
        'max',
        'median',
        'relative-l2',
        'weighted-l2',
        '99th percentile',
        '95th percentile',
        '90th percentile',
        'peakMemA',
        'peakMemB',
        'computeMappingTime']
    df[numeric_cols] = df[numeric_cols].apply(pandas.to_numeric)

    # remove all matching meshes
    df = df[df["mesh A"] != df["mesh B"]]

    singleB = df[df["mesh B"] == 0.025]

    # \item about the best way to go: for one target mesh compare best local-rbf (gaussian), global-rbf (tps), nn, np (For each geometry: 12 series)
    #   Goal: show errors of best mappings (user perspective)
    best = singleB[
        singleB["mapping"].apply(lambda n: (n in ["nn", "np", "tps"]) | n.endswith("-separate"))
    ]
    plot(best, "best-mappings", xname="mesh A", yname="relative-l2", show=args.show)

    # \item pick one geometry, one target mesh: nn, np, tps, gaussian-nX separate
    #   Goal: show memory usage of best mappings (user perspective)
    plot(singleB, "memory-usage", xname="mesh A", yname="peakMemB", show=args.show, conv=False)

    # \item pick one geometry, one target mesh: nn, np, tps, gaussian-nX separate
    #   Goal: show compute time of best mappings (user perspective)
    plot(singleB[singleB["computeMappingTime"] > 0], "compute-time",
         xname="mesh A", yname="computeMappingTime", show=args.show, conv=False)

    # \item pick one geometry, one target mesh, varying rank counts: nn, np, tps, gaussian-nX separate
    #   Goal: show weak scalability of best mappings (user perspective)
    # TODO plot(singleB, show=args.show)

    # \item pick one geometry, fixed rank count, varying target meshes: nn, np, tps, gaussian-nX separate
    #   Goal: show strong scalability of best mappings (user perspective)
    plot(singleB, "strong-scaling", xname="mesh A", yname="computeMappingTime", show=args.show, conv=False)

    # \item pick one geometry and target mesh: compare gaussian rbf on vs separate and different support radii (8 series)
    #   Goal: Options for local-rbf you should not choose and why
    gaussians = singleB[df["mapping"].str.startswith("gaussian")]
    plot(gaussians, "rbf-comp", xname="mesh A", yname="relative-l2", show=args.show)

    # \item pick one geometry: 3 different target meshes: np vs gaussian-n5-separate (6 series)
    #   Goal: Above holds for different target meshes
    reverse = df.query('mapping == "np" | mapping == "gaussian-n5-separate"')
    plot(reverse, "changing-b", xname="mesh A", yname="relative-l2", show=args.show)

    return 0


def plot(df, output, xname="mesh A", yname="relative-l2", groupname="mesh B", show=False, conv=True):
    fmt = "{} onto {}"
    styler = getStyler()

    print("Plot x:{} y:{} grouped by {}".format(xname, yname, groupname))

    df = df.sort_values(xname)
    grouped = df.groupby(["mapping", groupname])

    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(10, 5))

    for name, group in grouped:
        print("\tGroup {} with {} points".format(fmt.format(*name), group.shape[0]))
        l, m, c = next(styler)
        group.plot(
            ax=ax,
            loglog=True,
            x=xname,
            y=yname,
            label=fmt.format(*name),
            marker=m,
            linestyle=l,
            color=c
        )
    ax.set_xlabel("edge length(h) of {}".format(xname))
    ax.set_ylabel("{} error mapping to mesh B".format(yname))

    if conv:
        filtered = df[yname]
        plot_order(ax, 1, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())
        plot_order(ax, 2, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())
        plot_order(ax, 3, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())

    plt.gca().invert_xaxis()
    plt.grid()
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.subplots_adjust(right=0.7)

    if show:
        plt.show()
    else:
        parts = [output]
        parts.extend(".pdf")
        fig.savefig("".join(parts), pad_inches=1)


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
