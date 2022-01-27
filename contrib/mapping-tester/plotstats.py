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
    grouped = df.groupby(["mapping", "constraint"])

    ncols=2
    nrows = int(np.ceil(grouped.ngroups/ncols))

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12,4), sharey=True)

    for (key, ax) in zip(grouped.groups.keys(), axes.flatten()):
        grouped.get_group(key).plot(
            ax=ax,
            x="count",
            y=["relative-l2", "median"],
            loglog=True,
            title=str(key)
        )
        ax.set_xlabel("vertex count of mesh A")
        ax.set_ylabel("mapping error to mesh B")
        ax.legend()

    plt.show()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
