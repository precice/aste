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


def timingStats(dir: pathlib.Path, constraint: str):
    assert dir.is_dir()
    for cmd in ["merge", "export"]:
        assert (
            os.system(f"command -v precice-profiling-{cmd} > /dev/null") == 0
        ), 'Could not find the profiling tool "precice-profiling-{cmd}", which is part of the precice-profiling PiPy package.'
    event_dir = dir / "precice-profiling"
    timings_file = dir / "timings.csv"

    if not event_dir.is_dir():
        return {}

    try:
        subprocess.run(
            ["precice-profiling-merge", event_dir.absolute()],
            check=True,
            capture_output=True,
            cwd=dir,
        )
        subprocess.run(
            ["precice-profiling-export", "--output", timings_file.absolute()],
            check=True,
            capture_output=True,
            cwd=dir,
        )
        import polars as pl

        participant = "A" if constraint == "conservative" else "B"

        df = (
            pl.read_csv(timings_file)
            .filter(pl.col("participant") == participant)
            .select("event", "duration")
        )
        return {
            "globalTime": df.filter(pl.col("event") == "_GLOBAL")
            .select("duration")
            .max()
            .item(),
            "initializeTime": df.filter(pl.col("event") == "initialize")
            .select("duration")
            .max()
            .item(),
            "computeMappingTime": df.filter(
                pl.col("event").str.contains(
                    "^initialize/map..*.computeMapping.FromA-MeshToB-Mesh$"
                )
            )
            .select("duration")
            .max()
            .item(),
            "mapDataTime": df.filter(
                pl.col("event").str.contains(
                    "^advance/map..*.mapData.FromA-MeshToB-Mesh$"
                )
            )
            .select("duration")
            .max()
            .item(),
        }
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
    stats.update(timingStats(casedir, constraint))
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
