#! python3

import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt
import math

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), default="stats.csv", help='The CSV file containing the gathered stats.')
    return parser.parse_args(args)

def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))

def main(argv):
    args = parseArguments(argv[1:])

    df = pandas.read_csv(args.file)
    df.sort_values("mesh A", inplace=True)
    grouped = df.groupby(["mapping", "mesh B"])

    fig, ax = plt.subplots(sharex=True, sharey=True)

    for name, group in grouped:
        filtered = group # group[group["mesh A"] != group["mesh B"]]
        filtered.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y="relative-l2",
            label="{} onto {}".format(*name),
            marker="o"
        )
    ax.set_xlabel("edge length(h) of mesh A")
    ax.set_ylabel("relative-l2 error mapping to mesh B")

    # 1st order line
    fox = [0.0003, 0.1]
    foy1 = 1e-6
    foy2 = foy1 * (fox[1]/fox[0])
    foy = [foy1, foy2]
    ax.plot(fox, foy, color="lightgray", linewidth=1.0, zorder=-1)
    ax.annotate(
        "1st order",
        xy=(lavg(fox), lavg(foy)),
        color="gray",
        zorder=-1
    )

    # # 2nd order line
    sox = [0.0004, 0.01]
    soy1 = 3e-9
    soy2 = soy1 * ((sox[1]/sox[0])**2)
    soy = [soy1, soy2]
    ax.plot(sox, soy, color="lightgray", linewidth=1.0, zorder=-1)

    print( sox, soy)
    print( (sox[0] + sox[1])/2, (soy[0] + soy[1])/2)
    ax.annotate(
        "2nd order",
        xy=(lavg(sox), lavg(soy)),
        color="gray",
        zorder=-1
    )

    plt.gca().invert_xaxis()
    plt.grid()
    plt.show()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
