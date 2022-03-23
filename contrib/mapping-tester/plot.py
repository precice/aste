#! python3

import argparse
import pandas
import numpy as np
import matplotlib.pyplot as plt
import math

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Creates convergence plots from gathered stats")
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), default="stats.csv", help='The CSV file containing the gathered stats.')
    parser.add_argument('-o', '--outname', default="turbine", help='Name of the output pdfs')
    return parser.parse_args(args)

def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))

# seaborn.color_palette("colorblind", 10).as_hex()
style_colours = ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', '#ca9161', '#fbafe4', '#949494', '#ece133', '#56b4e9']
style_markers = ["o", "D", "s"]
styles = [ (c, m) for m in style_markers for c in style_colours]


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
    foy2 = foy1 * (fox[1]/fox[0])
    foy = [foy1, foy2]

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
    soy2 = soy1 * ((sox[1]/sox[0])**2)
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


def plotError(dfo, outname):
    select = [
        'nn', 'np', 'nng'
    ]
    df = dfo[dfo['mapping'].isin(select)]

    yname="relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)

    for grouped, style in zip(series, styles):
        name, group = grouped
        if (group[yname].max() == 0):
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
            color=color
        )
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping error")

    #plotConv(ax, df, yname, offsets=(0, 0))

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-error-best.pdf")


def plotMemory(dfo, outname, yname= "peakMemB"):
    select = [
        'nn', 'np', 'nng'
    ]
    df = dfo[dfo['mapping'].isin(select)]

    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for grouped, style in zip(series, styles):
       name, group = grouped
       if (group[yname].max() == 0):
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
            color=color
                )
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("peak memory [Bytes]")

    # evtl. add legend here
    #plotConv(ax, df, yname)

    #ax.set_yscale("log", base=2)
    #ax.set_ylim(ymin=2**math.floor(math.log2(df[yname].min())),
    #            ymax=2**math.ceil(math.log2(df[yname].max())) - 1)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-" + str(yname) + ".pdf")


def plotComputeMappingTime(dfo, outname):
    yname="computeMappingTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng"
    ])]

    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if (group[yname].max() == 0):
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
            color=color
        )

    ax.set_ylim(10, 10**7)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("preparation time [ms]")

    #plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-computed.pdf")


def plotMapDataTime(dfo, outname):
    yname="mapDataTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng"
    ])]

    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby(by="mapping", sort=False)
    for grouped, style in zip(series, styles):
        name, group = grouped
        if (group[yname].max() == 0):
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
            color=color
        )

    ax.set_ylim(1, 10**5)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("mapping time [ms]")

    #plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-mapped.pdf")

def plotReceiveDataTime(dfo, outname):
    yname="receiveDataTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng"
    ])]

    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh B",
            y=yname,
            label=name,
            marker=marker,
            color=color
        )

    ax.set_ylim(10, 10**7)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("receive data time [ms]")

    #plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-receiveDataTime.pdf")

def plotReceiveGradientDataTime(dfo, outname):
    yname="receiveGradientDataTime"
    df = dfo[dfo["mapping"].isin([
        "nn",
        "np",
        "nng"
    ])]

    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if (group[yname].max() == 0):
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x="mesh B",
            y=yname,
            label=name,
            marker=marker,
            color=color
        )

    ax.set_ylim(10, 10**7)
    ax.set_xlabel("mesh width h")
    ax.set_ylabel("receive gradient data time [ms]")

    #plotConv(ax, df, yname)

    plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(str(outname) + "-receiveGradientDataTime.pdf")

def main(argv):
    args = parseArguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    toMeshes = df["mesh B"].unique()
    assert len(toMeshes) == 1, f"There are {len(toMeshes)} to-meshes but only 1 is allowed. Fix your dataset!"
    df.sort_values("mesh A", inplace=True)
    plotError(df, args.outname)
    plotMemory(df, args.outname)
    plotMemory(df, args.outname, yname="peakMemA")
    plotMapDataTime(df, args.outname)
    plotComputeMappingTime(df, args.outname)
    plotReceiveDataTime(df, args.outname)
    plotReceiveGradientDataTime(df, args.outname)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
