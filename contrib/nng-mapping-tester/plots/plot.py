#! python3

import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt
import math
import itertools


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), default="stats.csv", help='The CSV file containing the gathered stats.')
    parser.add_argument('-ni', '--no-inverse', dest="inverse", action="store_false", help='Do not create inverse plots.')
    parser.add_argument('--show', action="store_true", help='Shows the plots insead of saving them.')
    return parser.parse_args(args)


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))


def getStyler():
    styles = ['solid', 'dashed', 'dashdot']
    colors = ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', '#ca9161', '#fbafe4', '#949494', '#ece133', '#56b4e9']
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
    numeric_cols = ['mesh A', 'mesh B', 'count', 'min', 'max', 'median', 'relative-l2', 'weighted-l2', '99th percentile', '95th percentile', '90th percentile']
    df[numeric_cols] = df[numeric_cols].apply(pandas.to_numeric)

    # A on x axes
    plot(df, False, True, args.show)
    plot(df, False, False, args.show)
    
    if (args.inverse):
        # B on x axes
        plot(df, True, True, args.show)
        plot(df, True, False, args.show)
    return 0


def plot(df, inverse, idfilter, show=False):
    if inverse:
        xname = "mesh B"
        groupname = "mesh A"
        fmt = "{} from {}"
    else:
        xname = "mesh A"
        groupname = "mesh B"
        fmt = "{} onto {}"
    yname="relative-l2"
    styler = getStyler()

    print("Plot x:{} y:{} grouped by {}".format(xname, yname, groupname))

    df.sort_values(xname, inplace=True)
    grouped = df.groupby(["mapping", groupname])

    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(10,5))

    for name, group in grouped:
        filtered = group[group["mesh A"] != group["mesh B"]] if idfilter else group
        print("\tGroup {} with {} points".format(fmt.format(*name), filtered.shape[0]))
        l, m, c = next(styler)
        filtered.plot(
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

    if(not inverse):
        filtered = df[df['mesh A'] != df['mesh B']][yname]
        plot_order(ax, 1, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())
        plot_order(ax, 2, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())
        plot_order(ax, 3, df[xname].min(), df[xname].max(), filtered.min(), filtered.max())

    plt.gca().invert_xaxis()
    plt.grid()
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
    plt.subplots_adjust(right=0.7)


    if show:
        plt.show()
    else:
        parts = ["plot"]
        if inverse:
            parts.extend("-inverse")
        if idfilter:
            parts.extend("-noid")
        parts.extend(".pdf")
        fig.savefig("".join(parts), pad_inches=1)


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
