#! python3

import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import math
import yaml
from functools import lru_cache


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))

@lru_cache
def getStyle():
    return yaml.load(open("style.yml").read(), Loader=yaml.BaseLoader)


def prettifyMapping(name):
    return getStyle()[name]["name"]


def orderFor(names):
    if (names.dtype == object):
        mappings = list(getStyle().keys())
        return names.map(mappings.index)
    else:
        return names


def styleFor(name):
    # Returns color marker line
    match = getStyle()[name]
    return match["color"], match["marker"], match["line"]


def plotConv(ax, df, yname, offsets=(0, 0)):
    xmin = df["mesh A"].min()
    xmax = df["mesh A"].max()
    ymin = df[yname].min() + offsets[0]
    ymax = df[yname].max() + offsets[1]

    convColor = "black"

    if (ymin == ymax or xmin == xmax):
        return

    # 1st order line
    fox = [xmax, xmin]
    foy1 = ymax
    foy2 = foy1 * (fox[1] / fox[0])
    foy = [foy1, foy2]
    if (foy1 == foy2):
        return

    ax.axline((fox[0], foy[0]), (fox[1], foy[1]),
              color=convColor,
              linewidth=1.0,
              zorder=-1)
    ax.annotate("1st order",
                va="bottom", ha="left",
                xy=(lavg(fox), lavg(foy)),
                color=convColor,
                zorder=-1)

    # # 2nd order line
    sox = [xmin, xmax]
    soy1 = ymin
    soy2 = soy1 * ((sox[1] / sox[0])**2)
    soy = [soy1, soy2]
    if (soy1 == soy2):
        return

    ax.axline((sox[0], soy[0]), (sox[1], soy[1]),
              color=convColor,
              linewidth=1.0,
              zorder=-1)
    ax.annotate("2nd order",
                va="top", ha="right",
                xy=(lavg(sox), lavg(soy)),
                color=convColor,
                zorder=-1)


def addlegend(ax):
    order = list(getStyle().keys())
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = zip(*sorted(zip(handles, labels), key=lambda p: order.index(p[1])))
    labels = list(map(prettifyMapping, labels))
    ax.xaxis.set_minor_formatter(matplotlib.ticker.LogFormatterMathtext())
    ax.legend(handles, labels,
              loc="upper center",
              bbox_to_anchor=(0.5, -.2),
              ncol=2,
              borderaxespad=0.,
              numpoints=2)


def plotError(df):
    plotErrorBest(df)
    #plotErrorLRBF(df)
    plotErrorRBFPoly(df)


def plotErrorBest(dfo):
    select = [
        'nn', 'np','nng', 'compact-tps-c2-n3-separate'
    ]
    df = dfo[dfo['mapping'].isin(select)]
    yname = "relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(ax=ax,
                   loglog=True,
                   x="mesh A",
                   y=yname,
                   label=name,
                   marker=marker,
                   linestyle=line,
                   color=color)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping error")
    addlegend(ax)

    plotConv(ax, df, yname, offsets=(-2e-6, 0.08))

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-error-best.pdf")


def plotErrorLRBF(dfo):
    remove = ['nn', 'np', 'tps']
    df = dfo[~dfo['mapping'].isin(remove)
             & ~dfo['mapping'].str.contains('.*-on')]
    yname = "relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(ax=ax,
                   loglog=True,
                   x="mesh A",
                   y=yname,
                   label=name,
                   marker=marker,
                   linestyle=line,
                   color=color)

    ax.set_ylim(1e-5, 0.03)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping error")
    addlegend(ax)

    plotConv(ax, df, yname, offsets=(-5e-6, 0.005))

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-error-localrbf.pdf")


def plotErrorRBFPoly(dfo):
    select = [    
        'compact-tps-c2-n3-on',
        'compact-tps-c2-n3-separate'
    ]
    df = dfo[dfo['mapping'].isin(select)]
    yname = "relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(ax=ax,
                   loglog=True,
                   x="mesh A",
                   y=yname,
                   label=name,
                   marker=marker,
                   linestyle=line,
                   color=color)
    ax.set_ylim(1e-4, 6e-2)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping error")
    addlegend(ax)

    plotConv(ax, df, yname, offsets=(-6e-5, 0))

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-error-poly.pdf")


def plotMemory(dfo):
    select = [
        'nn', 'np','nng',
        'compact-tps-c2-n3-separate'
    ]
    df = dfo[dfo['mapping'].isin(select)]
    yname = "peakMemB"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh A",
            y=yname,
            label=name,
            marker=marker,
            linestyle=line,
            color=color,
        )
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("peak memory [Bytes]")
    addlegend(ax)

    ax.set_yscale("log", base=2)
    ax.set_ylim(ymin=2**math.floor(math.log2(df[yname].min())),
                ymax=2**math.ceil(math.log2(df[yname].max())) - 1)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-peakMemB.pdf")


def plotComputeMappingTime(dfo):
    yname = "computeMappingTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng",
        "compact-tps-c2-n3-separate",
    ])]
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(ax=ax,
                   loglog=True,
                   x="mesh A",
                   y=yname,
                   label=name,
                   marker=marker,
                   linestyle=line,
                   color=color)
    ax.set_ylim(10, 10**7)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("preparation time [ms]")
    addlegend(ax)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-computed.pdf")


def plotMapDataTime(dfo):
    yname = "mapDataTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng",
        "compact-tps-c2-n3-separate",
    ])]
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for name, group in series:
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker, line = styleFor(name)
        group.plot(ax=ax,
                   loglog=True,
                   x="mesh A",
                   y=yname,
                   label=name,
                   marker=marker,
                   linestyle=line,
                   color=color)

    ax.set_ylim(1, 10**5)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping time [ms]")
    addlegend(ax)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig("turbine-big-mapped.pdf")


def plotSmall(file):
    df = pandas.read_csv(file)
    df.sort_values(by=["mapping", "mesh A"], inplace=True, key=orderFor)
    toMeshes = df["mesh B"].unique()
    assert len(
        toMeshes
    ) == 1, f"There are {len(toMeshes)} to-meshes but only 1 is allowed. Fix your dataset!"
    df.sort_values(by="mesh A", inplace=True)
    plotError(df)
    plotMemory(df)
    plotMapDataTime(df)
    plotComputeMappingTime(df)


def main():
    plt.style.use("style.mpl")
    plotSmall("turbine-big.csv")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
