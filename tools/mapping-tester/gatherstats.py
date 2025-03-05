#! /usr/bin/env python3

import argparse
import csv
import json
import os
import pathlib
import subprocess
from concurrent.futures import ThreadPoolExecutor


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Gathers stats after a run")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
        type=pathlib.Path,
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


def timingStats(dir: pathlib.Path):
    assert dir.is_dir()
    assert (
        os.system("command -v precice-profiling > /dev/null") == 0
    ), 'Could not find the profiling tool "precice-profiling", which is part of the preCICE installation.'
    event_dir = dir / "precice-profiling"
    json_file = dir / "profiling.json"
    timings_file = dir / "timings.csv"

    if not event_dir.is_dir():
        return {}

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
        stats = {}
        with open(timings_file, "r") as csvfile:
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


def memoryStats(dir: pathlib.Path):
    assert dir.is_dir()
    stats = {}
    for P in "A", "B":
        memfile = dir / f"memory-{P}.log"
        total = 0
        if memfile.is_file():
            try:
                with open(memfile, "r") as file:
                    total = sum([float(e) / 1.0 for e in file.readlines()])
            except BaseException:
                pass
        stats[f"peakMem{P}"] = total

    return stats


def mappingStats(dir: pathlib.Path):
    statFiles = list(dir.glob("*.stats.json"))
    if not statFiles:
        return {}

    statFile = statFiles[0]
    assert statFile.is_file()
    with open(statFile, "r") as jsonfile:
        return dict(json.load(jsonfile))


def gatherCaseStats(casedir: pathlib.Path):
    assert casedir.is_dir()
    parts = [casedir.name] + [p.name for p in casedir.parents]
    assert len(parts) >= 4
    ranks, meshes, constraint, mapping = parts[:4]
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
    stats.update(timingStats(casedir))
    stats.update(memoryStats(casedir))
    stats.update(mappingStats(casedir))
    return stats


def main(argv):
    args = parseArguments(argv[1:])

    cases = [d.parent for d in args.outdir.rglob("done")]

    if not cases:
        print(f"No cases found in {args.outdir.absolute()}")
        return 1

    allstats = []

    def wrapper(case):
        print(f"Found: {case.relative_to(args.outdir)}")
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
