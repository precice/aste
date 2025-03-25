#! /usr/bin/env python3

import argparse
import csv
import pathlib
import subprocess


def parseArguments():
    # assume both scripts to be in the same folder by default
    gatherstatsdefault = pathlib.Path(__file__).parent / "gatherstats.py"

    parser = argparse.ArgumentParser(
        description="Repeats all configured cases N times, gathers stats and merges the results into a single stats file."
    )
    parser.add_argument(
        "repetitions",
        metavar="N",
        type=int,
        help="How often to repeat the test case",
    )
    parser.add_argument(
        "-c",
        "--cases",
        default="cases",
        type=pathlib.Path,
        help="Directory of the cases.",
    )
    parser.add_argument(
        "-f",
        "--file",
        default="stats{}.csv",
        help="The resulting CSV file containing all stats. The {} will be replaced with -N for the Nth run.",
    )
    parser.add_argument(
        "-g",
        "--gatherstats",
        default=gatherstatsdefault,
        type=pathlib.Path,
        help="Path to the gatherstats script.",
    )
    return parser.parse_args()


def merge(repetitions: int, filefmt):
    destination = filefmt.format("")
    print(f"Merging to {destination}")
    merged = []
    for n in range(repetitions):
        with open(filefmt.format(f"-{n}")) as file:
            for row in csv.DictReader(file):
                row["run"] = n
                merged.append(row)

    with open(filefmt.format(""), "w") as file:
        writer = csv.DictWriter(file, merged[0].keys())
        writer.writeheader()
        writer.writerows(merged)


def run(repetitions: int, casesdir: pathlib.Path, filefmt, gatherstats: pathlib.Path):
    for n in range(repetitions):
        print(f"### Run {n+1} of {repetitions}", flush=True)

        # Run the actual cases
        subprocess.run(["bash", casesdir / "runall.sh"], check=True)

        # Postprocess the test cases
        subprocess.run(["bash", casesdir / "postprocessall.sh"], check=True)

        # Gather the generated statistics
        subprocess.run(
            ["python3", gatherstats, "--file", filefmt.format(f"-{n}")], check=True
        )

    merge(repetitions, filefmt)


def main():
    args = parseArguments()
    assert args.gatherstats.exists()
    assert "{}" in args.file
    run(args.repetitions, args.cases, args.file, args.gatherstats)


if __name__ == "__main__":
    main()
