#! python3

import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), default="stats.csv", help='The CSV file containing the gathered stats.')
    return parser.parse_args(args)


def main(argv):
    args = parseArguments(argv[1:])

    df = pandas.read_csv(args.file)
    df.sort_values("count", inplace=True)
    grouped = df.groupby("mapping")

    fig, ax = plt.subplots(sharex=True, sharey=True)

    for name, group in grouped:
        group.plot(
            ax=ax,
            loglog=True,
            x="count",
            y="relative-l2",
            label=str(name)
        )
    ax.set_xlabel("vertex count of mesh A")
    ax.set_ylabel("relative-l2 error mapping to mesh B")

    # 1st order line
    ax.plot([1e+3, 1e+5], [1e-5, 1e-7], color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate(
        "1st order",
        xy=(1e+4, 1e-6),
        color="gray",
        zorder=-1
    )

    # 2nd order line
    ax.plot([1e+3, 1e+5], [1e-5, 1e-9], color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate(
        "2nd order",
        xy=(1e+4, 1e-7),
        color="gray",
        zorder=-1
    )

    plt.show()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
