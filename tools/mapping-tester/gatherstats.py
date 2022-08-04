#! /usr/bin/env python3

import json
import csv
import os
import argparse
import glob


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Gathers stats after a run")
    parser.add_argument('-o', '--outdir', default="cases", help='Directory to generate the test suite in.')
    parser.add_argument('-f', '--file', type=argparse.FileType('w'), default="stats.csv",
                        help='The resulting CSV file containing all stats.')
    return parser.parse_args(args)


def statsFromTimings(dir):
    stats = {}
    assert(os.path.isdir(dir))
    file = os.path.join(dir, "precice-B-events.json")
    if os.path.isfile(file):
        try:
            timings = {}
            with open(file, "r") as jsonfile:
                timings = json.load(jsonfile)["Ranks"][0]["Timings"]
            stats["globalTime"] = timings["_GLOBAL"]["Max"]
            stats["initializeTime"] = timings["initialize"]["Max"]
            computeMappingName = [x for x in timings.keys() if x.startswith(
                "advance/map") and x.endswith("computeMapping.FromA-MeshToB-Mesh")][0]
            mapDataName = [x for x in timings.keys() if x.startswith(
                "advance/map") and x.endswith("mapData.FromA-MeshToB-Mesh")][0]
            stats["computeMappingTime"] = timings[computeMappingName]["Max"]
            stats["mapDataTime"] = timings[mapDataName]["Max"]
        except BaseException:
            pass
    return stats


def memoryStats(dir):
    stats = {}
    assert(os.path.isdir(dir))
    for P in "A", "B":
        memfile = os.path.join(dir, f"memory-{P}.log")
        total = 0
        if os.path.isfile(memfile):
            try:
                with open(memfile, "r") as file:
                    total = sum([float(e) / 1024.0 for e in file.readlines()])
            except BaseException:
                pass
        stats[f"peakMem{P}"] = total

    return stats


def main(argv):
    args = parseArguments(argv[1:])

    globber = os.path.join(args.outdir, "**", "*.stats.json")
    statFiles = [
        os.path.relpath(path, args.outdir)
        for path in glob.iglob(globber, recursive=True)
    ]
    allstats = []
    fields = []
    for file in statFiles:
        print("Found: " + file)
        casedir = os.path.join(args.outdir, os.path.dirname(file))
        parts = os.path.normpath(file).split(os.sep)
        assert(len(parts) >= 5)
        mapping, constraint, meshes, ranks, _ = parts[-5:]
        meshA, meshB = meshes.split('-')
        ranksA, ranksB = meshes.split('-')

        with open(os.path.join(args.outdir, file), "r") as jsonfile:
            stats = json.load(jsonfile)
            stats["mapping"] = mapping
            stats["constraint"] = constraint
            stats["mesh A"] = meshA
            stats["mesh B"] = meshB
            stats["ranks A"] = ranksA
            stats["ranks B"] = ranksB
            stats.update(statsFromTimings(casedir))
            stats.update(memoryStats(casedir))
            allstats.append(stats)
            if not fields:
                fields += stats.keys()

    assert(fields)
    writer = csv.DictWriter(args.file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(allstats)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
