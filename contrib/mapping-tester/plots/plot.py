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
    return parser.parse_args(args)

def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))

def getStyler():
    styles = ['solid', 'dashed', 'dashdot']
    colors = ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', '#ca9161', '#fbafe4', '#949494', '#ece133', '#56b4e9']
    markers = ['o', 'v', '^', 'D', '*']
    for style in itertools.product(styles, markers, colors):
        yield style


def main(argv):
    args = parseArguments(argv[1:])

    df = pandas.read_csv(args.file)
    numeric_cols = ['mesh A', 'mesh B', 'count', 'min', 'max', 'median', 'relative-l2', 'weighted-l2', '99th percentile', '95th percentile', '90th percentile']
    df[numeric_cols] = df[numeric_cols].apply(pandas.to_numeric)

    # A on x axes
    plot(df, False, True)
    plot(df, False, False)
    # B on x axes
    plot(df, True, True)
    plot(df, True, False)
    return 0


def plot(df, inverse, idfilter):
    if inverse:
        xname = "mesh B"
        groupname = "mesh A"
        fmt = "{} from {}"
    else:
        xname = "mesh A"
        groupname = "mesh B"
        fmt = "{} onto {}"
    styler = getStyler()

    df.sort_values(xname, inplace=True)
    grouped = df.groupby(["mapping", groupname])

    fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(10,8))

    for name, group in grouped:
        filtered = group[group["mesh A"] != group["mesh B"]] if idfilter else group
        verb = "from" if inverse else "onto"
        l, m, c = next(styler)
        filtered.plot(
            ax=ax,
            loglog=True,
            x=xname,
            y="relative-l2",
            label=fmt.format(*name),
            marker=m,
            linestyle=l,
            color=c
        )
    ax.set_xlabel("edge length(h) of {}".format(xname))
    ax.set_ylabel("relative-l2 error mapping to mesh B")

    # # 1st order line
    # fox = [0.0003, 0.1]
    # foy1 = 1e-6
    # foy2 = foy1 * (fox[1]/fox[0])
    # foy = [foy1, foy2]
    # ax.plot(fox, foy, color="lightgray", linewidth=1.0, zorder=-1)
    # ax.annotate(
    #     "1st order",
    #     xy=(lavg(fox), lavg(foy)),
    #     color="gray",
    #     zorder=-1
    # )

    # # # 2nd order line
    # sox = [0.0004, 0.01]
    # soy1 = 3e-9
    # soy2 = soy1 * ((sox[1]/sox[0])**2)
    # soy = [soy1, soy2]
    # ax.plot(sox, soy, color="lightgray", linewidth=1.0, zorder=-1)

    # ax.annotate(
    #     "2nd order",
    #     xy=(lavg(sox), lavg(soy)),
    #     color="gray",
    #     zorder=-1
    # )

    plt.gca().invert_xaxis()
    plt.grid()
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
    plt.subplots_adjust(right=0.75)


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
