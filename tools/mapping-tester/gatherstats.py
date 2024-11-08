#! /usr/bin/env python3

import argparse
import csv
import glob
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Gathers stats after a run")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("w"),
        default="stats.csv",
        help="The resulting CSV file containing all stats.",
    )
    return parser.parse_args(args)


def run_checked(args):
    r = subprocess.run(args, text=True, capture_output=True)
    if r.returncode != 0:
        print("Command " + " ".join(map(str, args)))
        print(f"Returncode {r.returncode}")
        print(r.stderr)
    r.check_returncode()


def statsFromTimings(dir):
    assert os.path.isdir(dir)
    assert (
        os.system("command -v precice-profiling > /dev/null") == 0
    ), 'Could not find the profiling tool "precice-profiling", which is part of the preCICE installation.'
    event_dir = os.path.join(dir, "precice-profiling")
    json_file = os.path.join(dir, "profiling.json")
    timings_file = os.path.join(dir, "timings.csv")

    try:
        subprocess.run(
            ["precice-profiling", "merge", "--output", json_file, event_dir],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["precice-profiling", "analyze", "--output", timings_file, "B", json_file],
            check=True,
            capture_output=True,
        )
        file = timings_file
        stats = {}
        with open(file, "r") as csvfile:
            timings = csv.reader(csvfile)
            for row in timings:
                if row[0] == "_GLOBAL":
                    stats["globalTime"] = row[-1]
                if row[0] == "initialize":
                    stats["initializeTime"] = row[-1]
                parts = row[0].split("/")
                event = parts[-1]
                if (
                    parts[0] == "initialize"
                    and event.startswith("map")
                    and event.endswith("computeMapping.FromA-MeshToB-Mesh")
                ):
                    stats["computeMappingTime"] = row[-1]
                if (
                    parts[0] == "advance"
                    and event.startswith("map")
                    and event.endswith("mapData.FromA-MeshToB-Mesh")
                ):
                    stats["mapDataTime"] = row[-1]
            return stats
    except:
        return {}


def memoryStats(dir):
    assert os.path.isdir(dir)
    stats = {}
    for P in "A", "B":
        memfile = os.path.join(dir, f"memory-{P}.log")
        total = 0
        if os.path.isfile(memfile):
            try:
                with open(memfile, "r") as file:
                    total = sum([float(e) / 1.0 for e in file.readlines()])
            except BaseException:
                pass
        stats[f"peakMem{P}"] = total

    return stats


def mappingStats(dir):
    globber = os.path.join(dir, "*.stats.json")
    statFiles = list(glob.iglob(globber))
    if len(statFiles) == 0:
        return {}

    statFile = statFiles[0]
    assert os.path.exists(statFile)
    with open(os.path.join(dir, statFile), "r") as jsonfile:
        return dict(json.load(jsonfile))


def gatherCaseStats(casedir):
    assert os.path.exists(casedir)
    parts = os.path.normpath(casedir).split(os.sep)
    assert len(parts) >= 5
    mapping, constraint, meshes, ranks = parts[-4:]
    meshA, meshB = meshes.split("-")
    ranksA, ranksB = ranks.split("-")

    stats = {
        "mapping": mapping,
        "constraint": constraint,
        "mesh A": meshA,
        "mesh B": meshB,
        "ranks A": ranksA,
        "ranks B": ranksB,
    }
    stats.update(statsFromTimings(casedir))
    stats.update(memoryStats(casedir))
    stats.update(mappingStats(casedir))
    return stats


def main(argv):
    args = parseArguments(argv[1:])

    globber = os.path.join(args.outdir, "**", "done")
    cases = [os.path.dirname(path) for path in glob.iglob(globber, recursive=True)]
    allstats = []

    def wrapper(case):
        print("Found: " + os.path.relpath(case, args.outdir))
        return gatherCaseStats(case)

    with ThreadPoolExecutor() as pool:
        for stat in pool.map(wrapper, cases):
            allstats.append(stat)

    fields = {key for s in allstats for key in s.keys()}
    assert fields
    writer = csv.DictWriter(args.file, fieldnames=sorted(fields))
    writer.writeheader()
    writer.writerows(allstats)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
