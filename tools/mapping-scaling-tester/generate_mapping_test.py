#! /usr/bin/env python3

import argparse
import json
import os
import sys

from common import *


def generate_cases(setup):
    meshes = setup["general"]["meshes"]
    network = setup["general"].get("network", "lo")
    syncmode = setup["general"].get("syncmode", "false")

    cases = []
    for group in setup["groups"]:
        for name, mapping in group["mapping"]["cases"].items():
            for constraint in group["mapping"]["constraints"]:
                for inname in group["meshes"]["A"]:
                    infile = meshes["A"][inname]
                    for outname in group["meshes"]["B"]:
                        outfile = meshes["B"][outname]
                        for ranksA, ranksB in zip(
                            as_iter(setup["general"]["ranks"].get("A", 1)),
                            as_iter(setup["general"]["ranks"].get("B", 1)),
                        ):
                            cases.append(
                                {
                                    "function": setup["general"]["function"],
                                    "mapping": {
                                        "name": name,
                                        "kind": mapping["kind"],
                                        "constraint": constraint,
                                        "options": mapping.get("options", ""),
                                    },
                                    "A": {
                                        "ranks": ranksA,
                                        "mesh": {
                                            "name": inname,
                                            "file": infile,
                                        },
                                    },
                                    "B": {
                                        "ranks": ranksB,
                                        "mesh": {
                                            "name": outname,
                                            "file": outfile,
                                        },
                                    },
                                    "network": network,
                                    "syncmode": syncmode,
                                }
                            )

    return cases


def parse_arguments(args):
    parser = argparse.ArgumentParser(description="Generator for a mapping test suite")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
    )
    parser.add_argument(
        "-s",
        "--setup",
        type=argparse.FileType("r"),
        default="setup.json",
        help="The test setup file to use.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=argparse.FileType("r"),
        default="config-template.xml",
        help="The precice config template to use.",
    )
    return parser.parse_args(args)


def main(argv):
    # Parse the input arguments
    args = parse_arguments(argv[1:])
    # Parse the json file using the json module
    setup = json.load(args.setup)
    # Read the xml-template file
    template = args.template.read()
    # Generate the actual cases
    cases = generate_cases(setup)
    outdir = os.path.normpath(args.outdir)
    if os.path.isdir(outdir):
        print('Warning: outdir "{}" already exisits.'.format(outdir))

    setup_cases(outdir, template, cases)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
