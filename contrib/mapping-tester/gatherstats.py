#! python3

import json
import csv
import os
import argparse
import glob

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Gathers stats after a run")
    parser.add_argument('-o', '--outdir', default="cases", help='Directory to generate the test suite in.')
    parser.add_argument('-f', '--file', type=argparse.FileType('w'), default="stats.csv", help='The resulting CSV file containing all stats.')
    return parser.parse_args(args)


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
        print("Found: "+file)
        parts = os.path.normpath(file).split(os.sep)
        assert(len(parts) >= 4)
        mapping, constraint, meshes, _ = parts[-4:]
        meshA, meshB = meshes.split('-')

        with open(os.path.join(args.outdir, file),"r") as jsonfile:
            stats = json.load(jsonfile)
            if not fields:
                fields += stats.keys()
            stats["mapping"] = mapping
            stats["constraint"] = constraint
            stats["mesh A"] = meshA
            stats["mesh B"] = meshB
            allstats.append(stats)

    fields = ["mapping", "constraint", "mesh A", "mesh B"] + fields
    writer = csv.DictWriter(args.file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(allstats)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
