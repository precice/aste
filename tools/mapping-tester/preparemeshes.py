#! /usr/bin/env python3

import argparse
import itertools
import json
import os
import shutil
import subprocess


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Prepares meshes for a test suite")
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
        "-f", "--force", action="store_true", help="Remove existing meshes."
    )

    return parser.parse_args(args)


def prepareMainMesh(meshdir, name, file, function, force=False):
    mainDir = os.path.join(meshdir, name, "1")
    mainMesh = os.path.join(mainDir, name + ".vtu")
    print("Preparing Mesh {} in {}".format(name, mainDir))

    if os.path.isdir(mainDir):
        if force:
            print("  Regenerating the mesh.")
            shutil.rmtree(mainDir)
        else:
            print("  Mesh already exists.")

            return

    os.makedirs(mainDir, exist_ok=True)
    data_name = "{}".format(function)
    [pathName, tmpfilename] = os.path.split(os.path.normpath(mainMesh))
    subprocess.run(
        [
            "precice-aste-evaluate",
            "--mesh",
            os.path.expandvars(file),
            "--function",
            function,
            "--data",
            data_name,
            "--directory",
            pathName,
            "-o",
            tmpfilename,
        ]
    )


def preparePartMesh(meshdir, name, p, force=False):

    if p == 1:
        return

    mainMesh = os.path.join(meshdir, name, "1", name + ".vtu")
    partDir = os.path.join(meshdir, name, str(p))
    partMesh = os.path.join(partDir, name)
    print("Preparing Mesh {} with {} paritions in {}".format(name, p, partDir))

    if os.path.isdir(partDir):
        if force:
            print("  Regenerating the partitioned mesh.")
            shutil.rmtree(partDir)
        else:
            print("  Partitioned mesh already exists.")

            return

    os.makedirs(partDir, exist_ok=True)
    [pathName, tmpfilename] = os.path.split(os.path.normpath(partMesh))
    subprocess.run(
        [
            "precice-aste-partition",
            "--mesh",
            mainMesh,
            "--algorithm",
            "topology",
            "-o",
            partMesh,
            "--directory",
            pathName,
            "-n",
            str(p),
        ]
    )


def main(argv):
    args = parseArguments(argv[1:])
    setup = json.load(args.setup)
    outdir = os.path.normpath(args.outdir)

    if os.path.isdir(outdir):
        print('Warning: outdir "{}" already exisits.'.format(outdir))
    meshdir = os.path.join(outdir, "meshes")
    function = setup["general"]["function"]

    partitions = set(
        [int(rank) for pranks in setup["general"]["ranks"].values() for rank in pranks]
    )

    for name, file in set(
        itertools.chain(
            setup["general"]["meshes"]["A"].items(),
            setup["general"]["meshes"]["B"].items(),
        )
    ):

        if not os.path.isfile(os.path.expandvars(file)):
            raise Exception(f'\033[91m Unable to open file called "{file}".\033[0m')
        prepareMainMesh(meshdir, name, file, function, args.force)

        for p in partitions:
            preparePartMesh(meshdir, name, p, args.force)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
